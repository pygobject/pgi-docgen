#!/usr/bin/python
# Copyright 2016 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""Debian related helpers.

This isn't used by pgidocgen, but by some of the included tools
"""

import os
import apt
import subprocess

from .debug import get_debug_files_for_name, get_debug_build_id_for_name
from .util import shell


def get_repo_typelibs():
    """Returns a dict of {package_name: [gir-name]},
    for example {"gir1.2-gtk-3.0": ["Gtk-3.0"]}
    """

    typelibs = {}
    data = subprocess.check_output(["apt-file", "search", ".typelib"])
    for line in data.strip().splitlines():
        package, path = line.split(": ", 1)
        if path.startswith("/usr/lib/x86_64-linux-gnu/girepository-1.0/") or \
                path.startswith("/usr/lib/girepository-1.0/"):
            name = os.path.splitext(os.path.basename(path))[0]
            typelibs.setdefault(package, set()).add(name)
    return typelibs


def get_repo_girs():
    """Returns a dict of {package_name: [gir-name]},
    for example {"libgtk-3-dev": ["Gtk-3.0"]}

    Note that this also finds things in stable/experimental, so
    apt-get downloading these might not give you a gir file in case the
    file moved to another package.
    """

    girs = {}
    data = subprocess.check_output(["apt-file", "search", ".gir"])
    for line in data.strip().splitlines():
        package, path = line.split(": ", 1)
        if path.startswith("/usr/share/gir-1.0/"):
            name = os.path.splitext(os.path.basename(path))[0]
            l = girs.setdefault(package, [])
            if name not in l:
                l.append(name)
    return girs


def _extract_control_field(field):
    """Extracts a field from debian control files for all packages"""

    ret, out, err = shell(
        "/usr/lib/apt/apt-helper cat-file "
        "$(apt-get indextargets --format '$(FILENAME)' | grep '.*Packages') | "
        "grep-dctrl -sPackage,%s --field=%s ''" % (field, field))
    assert ret == 0

    mapping = {}
    package = None
    for line in out.splitlines():
        if line.startswith("Package: "):
            package = line.split(":", 1)[-1].strip()
        elif line.startswith("%s: " % field):
            value = line.split(":", 1)[-1].strip()
            if not package:
                raise ValueError("no active package")
            # since we cat together multiple package sources
            # (testing/sid/experimental) we can get the same package multiple
            # times and thus get multiple values
            mapping.setdefault(package, []).append(value)

    return mapping


def get_build_ids():
    """Returns a mapping of all available build IDs in debian to the debug
    packages that contain the debug data.
    """

    build_ids = {}
    for package, values in _extract_control_field("Build-Ids").iteritems():
        for value in values:
            for v in value.split():
                build_ids[v] = package
    return build_ids


def get_debug_packages_for_libs(libraries):
    """For a sequence of shared libraries returns a mapping
    of shared libraries to packages holding the corresponding debug data.
    (in debian these are usually -dbg or -dbgsym packages)
    """

    # first get all possible debug file paths and look for them using
    # apt-file
    debug_files = set()
    for lib in libraries:
        debug_files.update(get_debug_files_for_name(lib))

    debug_packages = set()
    data = subprocess.check_output(["apt-file", "search", ".so"])
    data += subprocess.check_output(["apt-file", "search", ".debug"])
    for line in data.splitlines():
        package, path = line.split(": ", 1)
        if path in debug_files:
            debug_packages.add(package)

    # Since the new dbgsym repos in debian don't have Content files and
    # can't be searched using apt-file we have to parse the "Build-Ids"
    # value in the repo archives
    build_ids = get_build_ids()
    for lib in libraries:
        build_id = get_debug_build_id_for_name(lib)
        if build_id is not None and build_id in build_ids:
            debug_packages.add(build_ids[build_id])

    return debug_packages
