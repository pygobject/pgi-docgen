#!/usr/bin/env python3
# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import glob
import sys
import subprocess
import shutil
import requests
import time
from multiprocessing.pool import ThreadPool
from functools import cmp_to_key

from .debian import get_repo_girs, get_debug_packages_for_libs, \
    get_repo_typelibs, get_missing_lib_packages
from .util import parse_gir_shared_libs


DEB_SKIPLIST = [
    "gir1.2-hkl-5.0",
]

SKIPLIST = [
    # old gtk
    "Gtk-2.0",
    "Gdk-2.0",
    "GdkX11-2.0",
    'MateDesktop-2.0',
    'AtrilView-1.5.0',
    'AtrilDocument-1.5.0',
    'Eom-1.0',
    'Matekbd-1.0',

    # broken
    "Pluma-1.0",
    "Hkl-5.0",
    "Gcr-3",
    "GTop-2.0",
    "BraseroMedia-3.1",
    "Entangle-0.1",
    "Diodon-1.0",
    "Gee-0.8",
    "Skk-1.0",
    "SugarExt-1.0",
    'Nice-0.1',
    'BurnerMedia-3.1',
    'BurnerBurn-3.1',
    'Kkc-1.0',
    'Unity-7.0',  # invalid xml
    'UnityExtras-7.0',  # invalid xml

    # crashes
    'Granite-1.0',

    # depends on one of the above
    "GcrUi-3",
    "Caja-2.0",
    "MatePanelApplet-4.0",
    "BraseroBurn-3.1",
    "v_sim-3.7",

    # more broken things
    "AgsAudio-7.0",  # gir parsing

    "GIRepository-3.0",  # unclear

    "FPrint-2.0", # https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1122338

    "PQMarble-2",  # missing shared lib dep
    "Granite-7.0",  # missing shared lib
    "Folks-0.7",  # missing shared lib
    "FolksDummy-0.7",  # missing shared lib
    "FolksEds-0.7",  # missing shared lib
    "FolksTelepathy-0.7",  # missing shared lib
]


def check_typelibs(typelibs, install=False):
    import apt

    cache = apt.Cache()
    cache.open(None)

    to_install = set()
    for package in typelibs:
        if package in DEB_SKIPLIST:
            continue
        if cache[package].candidate is None:
            continue
        if not cache[package].is_installed:
            to_install.add(package)

    cache.close()

    handle_missing_packages(to_install, install=install)


def compare_deb_packages(a, b):
    import apt_pkg

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
    import apt

    dest = os.path.abspath(dest)
    assert not os.listdir(dest)

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
        girs = glob.glob(tmp_root + "/**/gir-1.0/*.gir", recursive=True)
        for src in girs:
            # in some cases when gir files move from share to lib there
            # are symlinks for backwards compat, just ignore them
            if os.path.islink(src):
                continue
            shutil.copy(src, dst)
        shutil.rmtree(tmp_root)


def fetch_girs_cached(cachedir):
    cachedir = "_debian_build_cache" if cachedir is None else cachedir
    cachedir = os.path.abspath(cachedir)
    if os.path.exists(cachedir):
        return cachedir
    os.makedirs(cachedir)
    print("find girs..")
    girs = get_repo_girs()
    print("fetch and extract debian packages..")
    fetch_girs(girs, cachedir)
    return cachedir


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
    import apt

    debug_packages = get_debug_packages_for_libs(shared_libs)

    cache = apt.Cache()
    cache.open(None)
    to_install = set()
    for package in sorted(debug_packages):
        if not cache[package].is_installed:
            if package.startswith(("libwebkit", "libjavascriptcore")):
                # 5GB of debug data.. nope
                continue
            if package in DEB_SKIPLIST:
                continue
            to_install.add(package)
    cache.close()

    handle_missing_packages(to_install, install=install)


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "create-debian", help="Create a sphinx environ for all of Debian")
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--no-build', action='store_true')
    parser.add_argument('--cachedir')
    parser.add_argument('target',
                        help='path to where the resulting source should be')
    parser.set_defaults(func=main)


def is_debian():
    return shutil.which("dpkg") is not None


def main(args):
    if not is_debian():
        raise SystemExit("Only available on debian")

    print("[don't forget to apt-file update/apt-get update!]")

    print("searching for typelibs..")
    typelibs = get_repo_typelibs()
    print("searching for uninstalled typelibs")
    check_typelibs(typelibs, args.install)

    data_dir = fetch_girs_cached(args.cachedir)
    gir_dir = os.path.join(data_dir, "gir-1.0")
    gir_list = [os.path.splitext(e)[0] for e in os.listdir(gir_dir)]

    typelib_ns = set()
    for namespaces in typelibs.values():
        typelib_ns.update(namespaces)

    print("Unknown in deb skiplist: %r" % sorted([p for p in DEB_SKIPLIST if p not in typelibs]))
    print("Unknown in typelib skiplist: %r" % sorted([n for n in SKIPLIST if n not in typelib_ns]))

    print("Missing gir files: %r" % sorted(typelib_ns - set(gir_list)))
    print("Missing typelib files: %r" % sorted(set(gir_list) - typelib_ns))
    can_build = sorted(set(gir_list) & typelib_ns)
    print("%d ready to build" % len(can_build))

    print("searching for required shared libraries..")
    shared_libs = get_gir_shared_libraries(gir_dir, can_build)
    check_shared_libs(shared_libs, args.install)

    print("searching for debug packages..")
    check_debug_packages(shared_libs, args.install)

    do_build = set(can_build) - set(SKIPLIST)
    print("%d ready to build after filtering" % len(do_build))

    if args.no_build:
        print("build skipped, done.")
        return

    print("starting the build..")
    os.environ["XDG_DATA_DIRS"] = data_dir
    subprocess.check_call(
        ["xvfb-run", "-a", sys.executable, sys.argv[0],
         "create", args.target] + sorted(do_build))
