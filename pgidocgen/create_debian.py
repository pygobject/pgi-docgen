#!/usr/bin/python3
# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import sys
import subprocess
import shutil
import requests
import time
from multiprocessing.pool import ThreadPool
from functools import cmp_to_key

import apt
import apt_pkg

from .debian import get_repo_girs, get_debug_packages_for_libs, \
    get_repo_typelibs, get_missing_lib_packages
from .util import parse_gir_shared_libs


DEB_BLACKLIST = [
    "gir1.2-hkl-5.0",
    "gir1.2-totem-plparser-1.0",
    "gir1.2-gpaste-6.0",
    "libgstreamer-gl1.0-0",
    "gir1.2-gconf-2.0",
]

BLACKLIST = [
    # old gtk
    "Gtk-2.0",
    "Gdk-2.0",
    "GdkX11-2.0",
    'MateDesktop-2.0',
    'AtrilView-1.5.0',
    'AtrilDocument-1.5.0',
    'Eom-1.0',
    'Matekbd-1.0',
    'GConf-2.0',

    # broken
    "Pluma-1.0",
    "Hkl-5.0",
    "Gcr-3",
    "GTop-2.0",
    "BraseroMedia-3.1",
    "FolksTelepathy-0.6",
    "Folks-0.6",
    "FolksEds-0.6",
    "Entangle-0.1",
    "Diodon-1.0",
    "Gee-0.8",
    "Skk-1.0",
    "SugarExt-1.0",
    "Meta-Muffin.0",
    "libisocodes-1.2.2",
    'Nice-0.1',
    "Geoclue-2.0",
    "Gtd-1.0",
    'BurnerMedia-3.1',
    'BurnerBurn-3.1',
    'CloudProviders-0.3.0',
    'Kkc-1.0',

    # hangs?
    'NMA-1.0',

    # crashes
    'GUPnPIgd-1.0',
    'Granite-1.0',
    'Midori-0.6',

    # depends on one of the above
    "Ganv-1.0",
    "DbusmenuGtk-0.4",
    "GcrUi-3",
    "Caja-2.0",
    "AppIndicator-0.1",
    "MatePanelApplet-4.0",
    "BraseroBurn-3.1",
    "v_sim-3.7",
    "FolksDummy-0.6",
    "Wnck-1.0",
    "AyatanaAppIndicator-0.1",
]


def check_typelibs(typelibs, install=False):
    cache = apt.Cache()
    cache.open(None)

    to_install = set()
    for package in typelibs:
        if package in DEB_BLACKLIST:
            continue
        if cache[package].candidate is None:
            continue
        if not cache[package].is_installed:
            to_install.add(package)

    cache.close()

    handle_missing_packages(to_install, install=install)


def compare_deb_packages(a, b):
    va = subprocess.check_output(["dpkg", "--field", a, "Version"]).strip()
    vb = subprocess.check_output(["dpkg", "--field", b, "Version"]).strip()
    va = va.decode("utf-8")
    vb = vb.decode("utf-8")
    return apt_pkg.version_compare(va, vb)


def _fetch(args):
    dest, uri = args
    e = None
    for i in range(5):
        try:
            r = requests.get(uri)
            r.raise_for_status()
        except requests.RequestException:
            time.sleep(i * i)
            continue
        break
    else:
        raise Exception(e)
    filename = uri.rsplit("/", 1)[-1]
    with open(os.path.join(dest, filename), "wb") as h:
        h.write(r.content)
    return uri


def fetch_girs(girs, dest):
    dest = os.path.abspath(dest)
    assert not os.path.exists(dest)

    tmp_root = os.path.join(dest, "temp_root")
    tmp_download = os.path.join(dest, "tmp_download")
    dst = os.path.join(dest, "gir-1.0")

    print("Download packages..")
    uris = []
    cache = apt.Cache()
    cache.open(None)
    # install anything that is a candidate or older
    # (is versions really ordered?)
    for name in girs:
        package = cache[name]
        ok = False
        for version in package.versions:
            if ok or package.candidate == version:
                ok = True
                if version.uri:
                    uris.append(version.uri)
    cache.close()

    os.makedirs(tmp_download)
    pool = ThreadPool(processes=10)
    for i, uri in enumerate(pool.imap_unordered(_fetch, [(tmp_download, u) for u in uris])):
        print("%d/%d" % (i + 1, len(uris)), uri)
    pool.close()
    pool.join()

    print("Extracting packages..")

    # sort, so older girs get replaced
    entries = [os.path.join(tmp_download, e) for e in os.listdir(tmp_download)]
    entries.sort(key=cmp_to_key(compare_deb_packages))

    os.mkdir(dst)
    for path in entries:
        subprocess.check_call(["dpkg", "-x", path, tmp_root])
        base_src = os.path.join(tmp_root, "usr", "share", "gir-1.0")
        if not os.path.isdir(base_src):
            continue
        for e in os.listdir(base_src):
            src = os.path.join(base_src, e)
            shutil.copy(src, dst)
        shutil.rmtree(tmp_root)


def fetch_girs_cached():
    env_dir = os.environ.get("PGI_DOCGEN_DEBIAN_DATA_DIR", None)
    if env_dir is not None:
        assert os.path.exists(env_dir)
        return env_dir
    temp_data = "_debian_build_cache"
    if not os.path.exists(temp_data):
        print("find girs..")
        girs = get_repo_girs()
        print("fetch and extract debian packages..")
        fetch_girs(girs, temp_data)
    return temp_data


def get_gir_shared_libraries(gir_dir, can_build):
    all_libs = set()
    for entry in os.listdir(gir_dir):
        name, ext = os.path.splitext(entry)
        if name not in can_build:
            continue
        libs = parse_gir_shared_libs(os.path.join(gir_dir, entry))
        all_libs.update(libs)
    return all_libs


def handle_missing_packages(to_install, install=False):
    if not to_install:
        return

    command = ["sudo", "apt", "install", "--no-install-recommends", "-y"] + sorted(to_install)
    if install:
        subprocess.run(command, check=True)
    else:
        print("Not all debug packages installed:\n")
        print(" ".join(command))
        raise SystemExit(1)


def check_shared_libs(shared_libs, install=False):
    # Some debian typelib packages are missing a dependency on the shared lib
    packages = get_missing_lib_packages(shared_libs)
    handle_missing_packages(packages, install=install)


def check_debug_packages(shared_libs, install=False):
    debug_packages = get_debug_packages_for_libs(shared_libs)

    cache = apt.Cache()
    cache.open(None)
    to_install = set()
    for package in sorted(debug_packages):
        if not cache[package].is_installed:
            if package.startswith(("libwebkit", "libjavascriptcore")):
                # 5GB of debug data.. nope
                continue
            if package in DEB_BLACKLIST:
                continue
            to_install.add(package)
    cache.close()

    handle_missing_packages(to_install, install=install)


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "create-debian", help="Create a sphinx environ for all of Debian")
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--no-build', action='store_true')
    parser.add_argument('target',
                        help='path to where the resulting source should be')
    parser.set_defaults(func=main)


def main(args):
    print("[don't forget to apt-file update/apt-get update!]")

    print("searching for typelibs..")
    typelibs = get_repo_typelibs()
    print("searching for uninstalled typelibs")
    check_typelibs(typelibs, args.install)

    data_dir = fetch_girs_cached()
    gir_dir = os.path.join(data_dir, "gir-1.0")
    gir_list = [os.path.splitext(e)[0] for e in os.listdir(gir_dir)]

    typelib_ns = set()
    for namespaces in typelibs.values():
        typelib_ns.update(namespaces)

    print("Missing gir files: %r" % sorted(typelib_ns - set(gir_list)))
    print("Missing typelib files: %r" % sorted(set(gir_list) - typelib_ns))
    can_build = sorted(set(gir_list) & typelib_ns)
    print("%d ready to build" % len(can_build))

    can_build = set(can_build) - set(BLACKLIST)
    print("%d ready to build after blacklisting" % len(can_build))

    print("searching for required shared libraries..")
    shared_libs = get_gir_shared_libraries(gir_dir, can_build)
    check_shared_libs(shared_libs, args.install)

    print("searching for debug packages..")
    check_debug_packages(shared_libs, args.install)

    if args.no_build:
        print("build skipped, done.")
        return

    print("starting the build..")
    os.environ["XDG_DATA_DIRS"] = data_dir
    subprocess.check_call(
        ["xvfb-run", "-a", sys.executable, sys.argv[0],
         "create", args.target] + sorted(can_build))
