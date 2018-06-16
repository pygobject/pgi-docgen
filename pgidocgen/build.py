# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import io
import glob
import re
import subprocess
from multiprocessing.pool import ThreadPool
import multiprocessing
import threading
import shutil
import sys

import jinja2
import sphinx

from .mergeindex import mergeindex
from .util import rest2html
from .gen.genutil import get_data_dir


DEVHELP_PREFIX = "python-"


def get_cpu_count():
    try:
        return multiprocessing.cpu_count()
    except NotImplementedError:
        return 2


def rewrite_static_links(main):
    """Rerites the html <link> tags to reference the shared static dir.

    This helps to reduce http requests in the online case.
    """

    def rewrite(path, depth):
        with io.open(path, "r", encoding="utf-8") as h:
            data = h.read()

        def repl(match):
            href = match.group(2)
            if href.startswith("_static/"):
                start = 0
            elif "/_static/" in href:
                start = href.index("/_static/") + 1
            else:
                return "".join(match.groups())

            href = "../" * depth + href[start:]
            return match.group(1) + href

        new_data = re.sub("(<link .*? href=[\"'])([^\"']+)", repl, data)
        if data != new_data:
            with io.open(path, "w", encoding="utf-8") as h:
                h.write(new_data)

    for root, dirs, files in os.walk(main):
        if root == main:
            # ignore anything in the toplevel path
            continue
        for name in files:
            path = os.path.join(root, name)
            ext = os.path.splitext(path)[1]
            if ext != ".html":
                continue
            depth = os.path.relpath(main, path).count(os.sep)
            rewrite(path, depth)


def share_static(main):
    """Makes the sphinx _static folder shared.

    Can be run multiple times to dedup newly added modules.
    """

    rewrite_static_links(main)

    roots = []
    for entry in os.listdir(main):
        if entry.startswith(("_", ".")) or "-" not in entry:
            continue
        path = os.path.join(main, entry)
        if not os.path.isdir(path):
            continue
        roots.append(path)

    shared = os.path.join(main, "_static")

    if not os.path.exists(shared):
        # copy one to the root
        shutil.rmtree(shared, ignore_errors=True)
        shutil.copytree(os.path.join(roots[0], "_static"), shared)

    # remove all others
    for root in roots:
        static = os.path.join(root, "_static")
        shutil.rmtree(static, ignore_errors=True)


def do_build(package):
    print("Build started for %s" % package.name)

    sphinx_args = [package.path, package.build_path]
    copy_env = os.environ.copy()

    if package.devhelp:
        sphinx_args = ["-b", "devhelpfork"] + sphinx_args
        copy_env["PGIDOCGEN_TARGET_PREFIX"] = DEVHELP_PREFIX
    else:
        sphinx_args = ["-b", "html"] + sphinx_args
        copy_env["PGIDOCGEN_TARGET_PREFIX"] = ""

    copy_env["PGIDOCGEN_TARGET_BASE_PATH"] = \
        os.path.dirname(package.build_path)

    subprocess.check_call(
        [sys.executable, "-m", "sphinx", "-n", "-q", "-a", "-E"] + sphinx_args,
        env=copy_env)

    # we don't rebuild, remove all caches
    shutil.rmtree(os.path.join(package.build_path, ".doctrees"))
    os.remove(os.path.join(package.build_path, ".buildinfo"))

    # remove some pages we don't need
    os.remove(os.path.join(package.build_path, "genindex.html"))
    os.remove(os.path.join(package.build_path, "search.html"))

    if os.name != "nt":
        for d in ["structs", "unions", "interfaces", "iface-structs",
                  "class-structs"]:
            os.symlink("classes", os.path.join(package.build_path, d))

    return package


class Package(object):

    def __init__(self, name, lib_version, path, build_path, deps,
                 devhelp=False):
        self.name = name
        self.lib_version = lib_version
        self.path = path
        self.build_path = build_path
        self.deps = deps
        self.devhelp = devhelp

    def can_build(self, done_deps):
        return not (self.deps - set([p.name for p in done_deps]))

    def __repr__(self):
        return "<%s name=%s>" % (type(self).__name__, self.name)


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "build",
        help="build the sphinx environ created with pgi-docgen")
    parser.add_argument('source', help='path to the sphinx environ base dir')
    parser.add_argument('target',
                        help='path to where the resulting build should be')
    parser.add_argument('--devhelp', action='store_true')
    parser.set_defaults(func=main)


def main(args):
    if sphinx.version_info < (1, 5, 0):
        raise SystemExit("Needs sphinx 1.5.0+")

    to_build = {}

    target_path = os.path.abspath(args.target)
    devhelp = args.devhelp

    for entry in os.listdir(args.source):
        if entry.startswith("_"):
            continue
        path = os.path.join(args.source, entry)

        # extract the build dir from the config
        conf_path = os.path.join(path, "conf_data.py")
        with io.open(conf_path, "r", encoding="utf-8") as h:
            exec_env = {}
            exec(h.read(), exec_env)
        deps = set(exec_env["DEPS"])
        if devhelp:
            prefix = DEVHELP_PREFIX
        else:
            prefix = ""
        lib_version = exec_env["LIB_VERSION"]

        build_path = os.path.join(target_path, prefix + entry)

        package = Package(entry, lib_version, path, build_path, deps, devhelp)
        to_build[package.name] = package

    if not to_build:
        raise SystemExit("Nothing to build")

    # don't build cairo-1.0, we reference the external one
    to_ignore = set([])
    for ignore in ["cairo-1.0"]:
        p = to_build.pop(ignore, None)
        if p:
            to_ignore.add(p)

    try:
        os.mkdir(target_path)
    except OSError:
        pass

    # build bottom up
    done = set()
    num_to_build = len(to_build)
    pool = ThreadPool(int(get_cpu_count() * 1.5))
    event = threading.Event()

    def job_cb(package=None):
        if package is not None:
            done.add(package)
            print("%s finished: %d/%d done" % (
                  package.name, len(done), num_to_build))

        for package in get_new_jobs():
            print("Queue build for %s" % package.name)
            pool.apply_async(do_build, [package], callback=job_cb)

        if len(done) == num_to_build:
            print("All done")
            event.set()

    def get_new_jobs():
        jobs = []

        done_deps = done | to_ignore
        for name, package in list(to_build.items()):
            if package.can_build(done_deps):
                del to_build[name]
                jobs.append(package)

        return jobs

    for name, package in list(to_build.items()):
        if os.path.exists(package.build_path):
            del to_build[name]
            done.add(package)

    job_cb()
    event.wait()
    pool.close()
    pool.join()

    if not devhelp:
        mergeindex(target_path)

        index_path = os.path.join(get_data_dir(), "index")
        for entry in os.listdir(index_path):
            src = os.path.join(index_path, entry)
            dst = os.path.join(target_path, entry)
            shutil.copyfile(src, dst)

        done_sorted = sorted(done, key=lambda d: d.name.lower())
        results = [(d.name + "/index.html", d.name.split("-")[0],
                    d.name.split("-")[-1], d.lib_version)
                   for d in done_sorted]
        with io.open(os.path.join(index_path, "sidebar.html"), "r", encoding="utf-8") as h:
            data = h.read()
        with io.open(os.path.join(target_path, "sidebar.html"), "w", encoding="utf-8") as t:
            env = jinja2.Environment().from_string(data)
            t.write(env.render(results=results))

        with io.open(os.path.join(index_path, "config.html"), "r", encoding="utf-8") as h:
            data = h.read()
        with io.open(os.path.join(target_path, "config.html"), "w", encoding="utf-8") as t:
            env = jinja2.Environment().from_string(data)
            t.write(env.render(results=results))

        with io.open(os.path.join(index_path, "faq.html"), "r", encoding="utf-8") as h:
            data = h.read()
        with io.open(os.path.join(get_data_dir(), "faq.rst"), "r", encoding="utf-8") as h:
            main_rst = h.read()
        with io.open(os.path.join(target_path, "faq.html"), "w", encoding="utf-8") as t:
            env = jinja2.Environment().from_string(data)
            t.write(env.render(body=rest2html(main_rst)))

        with io.open(os.path.join(index_path, "main.html"), "r", encoding="utf-8") as h:
            data = h.read()
        with io.open(os.path.join(target_path, "main.html"), "w", encoding="utf-8") as t:
            env = jinja2.Environment().from_string(data)
            t.write(env.render())

        share_static(target_path)
    else:
        # for devhelp to pick things up the dir name has to match the
        # devhelp file name (without the extension)
        for package in done:
            path = package.build_path
            dh = glob.glob(os.path.join(path, "*.devhelp2.gz"))[0]
            dh_name = os.path.join(
                os.path.dirname(dh), os.path.basename(path) + ".devhelp2.gz")
            if not os.path.exists(dh_name):
                os.rename(dh, dh_name)
