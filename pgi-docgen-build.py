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
import signal
import glob
import argparse
import subprocess
from multiprocessing.pool import ThreadPool
import multiprocessing
import threading
import shutil

from jinja2 import Template


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


def do_build(entry, path, build_path, devhelp):
    print "Build started for %s" % entry

    sphinx_args = [path, build_path]

    if devhelp:
        sphinx_args = ["-b", "devhelpfork"] + sphinx_args
    else:
        sphinx_args = ["-b", "html"] + sphinx_args

    subprocess.check_call(["sphinx-build", "-a", "-E"] + sphinx_args)

    # we don't rebuild, remove all caches
    shutil.rmtree(os.path.join(build_path, ".doctrees"))
    os.remove(os.path.join(build_path, ".buildinfo"))

    if has_optipng():
        png_dirs = [
            os.path.join(build_path, "_static"),
            os.path.join(build_path, "_images")
        ]

        for dir_ in png_dirs:
            png_optimize_dir(dir_)
    else:
        print "optipng missing, skipping compression"

    return entry


def main(argv):

    parser = argparse.ArgumentParser(
        description='Build the sphinx environ created with pgi-docgen')
    parser.add_argument('source', help='path to the sphinx environ base dir')
    parser.add_argument('--devhelp', action='store_true')
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
        build_path = os.path.join(target_path, entry)

        to_build[entry] = (path, build_path, deps)

    if not to_build:
        raise SystemExit("Nothing to build")

    to_ignore = set(["cairo-1.0"])

    # don't build cairo-1.0, we reference the external one
    for ignore in to_ignore:
        to_build.pop(ignore, None)

    try:
        os.mkdir(target_path)
    except OSError:
        pass

    if not args.devhelp:
        with open(os.path.join("data", "index.html"), "rb") as h:
            template = Template(h.read())

        with open(os.path.join(target_path, "index.html"), "wb") as h:
            h.write(template.render(entries=sorted(to_build.keys())))

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

    def job_cb(entry=None):
        if entry is not None:
            done.add(entry)
            print "%s finished: %d/%d done" % (
                entry, len(done), num_to_build)

        for entry, (path, build_path) in get_new_jobs():
            print "Queue build for %s" % entry
            pool.apply_async(
                do_build,
                [entry, path, build_path, args.devhelp],
                callback=job_cb)

        if len(done) == num_to_build:
            print "All done"
            event.set()

    def get_new_jobs():
        jobs = []

        for entry, (path, build_path, deps) in to_build.items():
            deps.difference_update(done)
            deps.difference_update(to_ignore)

        for entry, (path, build_path, deps) in to_build.items():
            if not deps:
                del to_build[entry]
                jobs.append([entry, (path, build_path)])

        return jobs

    for entry, (path, build_path, deps) in to_build.items():
        if os.path.exists(build_path):
            del to_build[entry]
            done.add(entry)

    job_cb()
    event.wait()
    pool.close()
    pool.join()

    # for devhelp to pick things up the dir name has to match the
    # devhelp file name (without the extension)
    if args.devhelp:
        for entry in done:
            path = os.path.join(target_path, entry)
            os.remove(os.path.join(path, "objects.inv"))
            dh = glob.glob(os.path.join(path, "*.devhelp.gz"))[0]
            dh_name = os.path.join(
                os.path.dirname(dh), entry + ".devhelp.gz")
            os.rename(dh, dh_name)


if __name__ == "__main__":
    main(sys.argv)
