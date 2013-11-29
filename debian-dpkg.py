#!/usr/bin/python
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""
usage: debian-dpkg.py [-h] namespaces [namespaces ...]

List installed debian package names for gir files

positional arguments:
  namespaces  list of namespaces including versions (e.g. "Gtk-3.0
              GLib-2.0")
"""

import subprocess
import argparse

from pgidocgen.util import get_gir_files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='List installed debian package names for gir files')

    parser.add_argument(
        'namespaces', nargs='+', help='list of namespaces '
        'including versions (e.g. "Gtk-3.0 GLib-2.0")')

    args = parser.parse_args()
    girs = get_gir_files()

    filtered = {}
    for name in args.namespaces:
        if name not in girs:
            print "GIR file for %s not found, aborting." % name
            raise SystemExit(1)
        filtered[name] = girs[name]

    packages = []
    for name, path in filtered.iteritems():
        out = subprocess.check_output(["dpkg", "-S", path])
        packages.append(out.split(":", 1)[0])
    packages = list(set(packages))
    packages.sort()

    print "sudo apt-get install " + " ".join(packages)
