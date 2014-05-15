#!/usr/bin/python
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""
usage: pgi-docgen-build.py [-h] source

Build the sphinx environ created with pgi-docgen

positional arguments:
  source      path to the sphinx environ base dir
"""

import os
import sys
import glob
import argparse
import subprocess
from multiprocessing.pool import ThreadPool
import multiprocessing
import threading
import shutil
import tarfile


OPTIPNG = "optipng"


def get_cpu_count():
    try:
        return multiprocessing.cpu_count()
    except NotImplementedError:
        return 2


def has_optipng():
    try:
        subprocess.check_output([OPTIPNG, "--version"])
    except OSError:
        return False
    return True


def png_optimize_dir(dir_, pool_size=6):
    """Optimizes all pngs in dir_ (non-recursive)"""

    if not os.path.exists(dir_):
        return

    print "optipng: %r" % dir_
    pngs = [e for e in os.listdir(dir_) if e.lower().endswith(".png")]
    paths = [os.path.join(dir_, f) for f in pngs]

    def _do_optimize(path):
        subprocess.check_output([OPTIPNG, path])

    pool = ThreadPool(pool_size)
    pool.map(_do_optimize, paths)
    pool.close()
    pool.join()


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

    if package.devhelp:
        sphinx_args = ["-b", "devhelpfork"] + sphinx_args
    else:
        sphinx_args = ["-b", "html"] + sphinx_args

    subprocess.check_call(["sphinx-build", "-a", "-E"] + sphinx_args)

    # we don't rebuild, remove all caches
    shutil.rmtree(os.path.join(package.build_path, ".doctrees"))
    os.remove(os.path.join(package.build_path, ".buildinfo"))

    if has_optipng():
        png_dirs = [
            os.path.join(package.build_path, "_static"),
            os.path.join(package.build_path, "_images")
        ]

        for dir_ in png_dirs:
            png_optimize_dir(dir_)
    else:
        print "optipng missing, skipping compression"

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


def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def main(argv):

    parser = argparse.ArgumentParser(
        description='Build the sphinx environ created with pgi-docgen')
    parser.add_argument('source', help='path to the sphinx environ base dir')
    args = parser.parse_args(argv[1:])

    to_build = {}

    for entry in os.listdir(args.source):
        if entry.startswith("_"):
            continue
        path = os.path.join(args.source, entry)

        # extract the build dir from the config
        conf_path = os.path.join(path, "_pgi_docgen_conf.py")
        with open(conf_path, "rb") as h:
            exec_env = {}
            exec h.read() in exec_env
        target_path = exec_env["TARGET"]
        deps = set(exec_env["DEPS"])
        devhelp = exec_env["DEVHELP_PREFIX"]
        build_path = os.path.join(target_path, devhelp + entry)

        package = Package(entry, path, build_path, deps, bool(devhelp))
        to_build[package.name] = package

    if not to_build:
        raise SystemExit("Nothing to build")

    devhelp = package.devhelp

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

    if not devhelp:
        index_path = os.path.join("data", "index")
        for entry in os.listdir(index_path):
            src = os.path.join(index_path, entry)
            dst = os.path.join(target_path, entry)
            shutil.copyfile(src, dst)

        static_target = os.path.join(target_path, "_static")
        if not os.path.exists(static_target):
            shutil.copytree(
                os.path.join("data", "theme", "static"),
                static_target)

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
        from pgidocgen.mergeindex import merge
        merge(target_path, include_terms=False)

    # add symlinks for the old layout
    if not devhelp:
        old_api = os.path.join(target_path, "api")
        try:
            os.mkdir(old_api)
        except OSError:
            pass

        for entry in os.listdir(target_path):
            if entry.startswith("_") or not "-" in entry:
                continue
            dir_ = os.path.join(target_path, entry)
            if not os.path.isdir(dir_):
                continue

            source = os.path.join("..", entry)
            try:
                # we need both names since the new modules
                # use relative urls with the new names
                target = os.path.join(old_api, entry.replace("-", "_"))
                os.symlink(source, target)
                target = os.path.join(old_api, entry)
                os.symlink(source, target)
            except Exception as e:
                # unix only
                pass

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
            tar_path = os.path.join(
                os.path.dirname(path),
                "devhelp-" + os.path.basename(path)  + ".tar.gz")
            make_tarfile(tar_path, path)
            shutil.rmtree(path)


if __name__ == "__main__":
    main(sys.argv)
