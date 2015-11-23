# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import glob
import argparse
import subprocess
from multiprocessing.pool import ThreadPool
import multiprocessing
import threading
import shutil

import jinja2
import sphinx

from .mergeindex import merge
from .util import rest2html
from .gen.genutil import get_data_dir


DEVHELP_PREFIX = "python-"


def get_cpu_count():
    try:
        return multiprocessing.cpu_count()
    except NotImplementedError:
        return 2


def share_static(main):
    """Makes the sphinx _static folder shared by symlinking it.

    Can be run multiple times to dedup newly added modules.
    """

    roots = []
    for entry in os.listdir(main):
        if entry.startswith(("_", ".")) or not "-" in entry:
            continue
        path = os.path.join(main, entry)
        if not os.path.isdir(path):
            continue
        roots.append(path)

    shared = os.path.join(main, "_shared_static")

    for root in roots:
        static = os.path.join(root, "_static")
        if os.path.islink(static):
            continue
        if not os.path.exists(shared):
            shutil.move(static, shared)
        else:
            shutil.rmtree(static)
        rel_target = os.path.relpath(shared, os.path.dirname(static))
        os.symlink(rel_target, static)


def do_build(package):
    print "Build started for %s" % package.name

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

    subprocess.check_call(["sphinx-build", "-j4", "-a", "-E"] + sphinx_args,
                          env=copy_env)

    # we don't rebuild, remove all caches
    shutil.rmtree(os.path.join(package.build_path, ".doctrees"))
    os.remove(os.path.join(package.build_path, ".buildinfo"))

    # remove some pages we don't need
    os.remove(os.path.join(package.build_path, "genindex.html"))
    os.remove(os.path.join(package.build_path, "search.html"))

    return package


class Package(object):

    def __init__(self, name, path, build_path, deps, devhelp=False):
        self.name = name
        self.path = path
        self.build_path = build_path
        self.deps = deps
        self.devhelp = devhelp

    def can_build(self, done_deps):
        return not (self.deps - set([p.name for p in done_deps]))

    def __repr__(self):
        return "<%s name=%s>" % (type(self).__name__, self.name)


def main(argv):

    parser = argparse.ArgumentParser(
        description='Build the sphinx environ created with pgi-docgen')
    parser.add_argument('source', help='path to the sphinx environ base dir')
    parser.add_argument('target',
                        help='path to where the resulting build should be')
    parser.add_argument('--devhelp', action='store_true')
    args = parser.parse_args(argv[1:])

    if sphinx.version_info < (1, 3):
        raise SystemExit("Needs sphinx 1.3+")

    to_build = {}

    target_path = os.path.abspath(args.target)
    devhelp = args.devhelp

    for entry in os.listdir(args.source):
        if entry.startswith("_"):
            continue
        path = os.path.join(args.source, entry)

        # extract the build dir from the config
        conf_path = os.path.join(path, "_pgi_docgen_conf.py")
        with open(conf_path, "rb") as h:
            exec_env = {}
            exec h.read() in exec_env
        deps = set(exec_env["DEPS"])
        if devhelp:
            prefix = DEVHELP_PREFIX
        else:
            prefix = ""

        build_path = os.path.join(target_path, prefix + entry)

        package = Package(entry, path, build_path, deps, devhelp)
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
            print "%s finished: %d/%d done" % (
                package.name, len(done), num_to_build)

        for package in get_new_jobs():
            print "Queue build for %s" % package.name
            pool.apply_async(do_build, [package], callback=job_cb)

        if len(done) == num_to_build:
            print "All done"
            event.set()

    def get_new_jobs():
        jobs = []

        done_deps = done | to_ignore
        for name, package in to_build.items():
            if package.can_build(done_deps):
                del to_build[name]
                jobs.append(package)

        return jobs

    for name, package in to_build.items():
        if os.path.exists(package.build_path):
            del to_build[name]
            done.add(package)

    job_cb()
    event.wait()
    pool.close()
    pool.join()

    print "#" * 37
    print "Creating index + search..."

    if not devhelp:
        print repr(target_path)
        merge(target_path, include_terms=False, exclude_old=True)

        index_path = os.path.join(get_data_dir(), "index")
        for entry in os.listdir(index_path):
            src = os.path.join(index_path, entry)
            dst = os.path.join(target_path, entry)
            shutil.copyfile(src, dst)

        done_sorted = sorted(done, key=lambda d: d.name.lower())
        results = [(d.name + "/index.html", d.name) for d in done_sorted]
        with open(os.path.join(index_path, "sidebar.html"), "rb") as h:
            data = h.read()
        with open(os.path.join(target_path, "sidebar.html"), "wb") as t:
            env = jinja2.Environment().from_string(data)
            t.write(env.render(results=results))

        with open(os.path.join(index_path, "main.html"), "rb") as h:
            data = h.read()
        with open(os.path.join(get_data_dir(), "main.rst"), "rb") as h:
            main_rst = h.read()
        with open(os.path.join(target_path, "main.html"), "wb") as t:
            env = jinja2.Environment().from_string(data)
            t.write(env.render(body=rest2html(main_rst)))

        static_target = os.path.join(target_path, "_static")
        if not os.path.exists(static_target):
            shutil.copytree(
                os.path.join(get_data_dir(), "theme", "static"),
                static_target)

    if not devhelp and os.name != "nt":
        share_static(target_path)

    # for devhelp to pick things up the dir name has to match the
    # devhelp file name (without the extension)
    if devhelp:
        for package in done:
            path = package.build_path
            os.remove(os.path.join(path, "objects.inv"))
            dh = glob.glob(os.path.join(path, "*.devhelp.gz"))[0]
            dh_name = os.path.join(
                os.path.dirname(dh), os.path.basename(path) + ".devhelp.gz")
            os.rename(dh, dh_name)
