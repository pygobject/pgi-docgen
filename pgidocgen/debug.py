# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import sys
import subprocess

"""
Provides source paths and line numbers for shared libraries.
The library has to include debug symbols or a separate debug symbol file has
to be present (same requirements as for gdb to display line numbers)

Check out get_line_numbers()
"""


def get_debug_file_directory():
    """Returns the directory where separate debug symbols can be found

    TODO: Don't hard code this? See "show debug-file-directory" in gdb
    """

    return "/usr/lib/debug"


def get_debug_file(library_path):
    """Returns the name of the linked debug library or None

    FIXME: this doesn't work with glib/gobject
    """

    library_path = os.path.abspath(library_path)
    try:
        data = subprocess.check_output(["readelf", "-p", ".gnu_debuglink",
                                        library_path],
                                        stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        return None

    for line in data.splitlines():
        line = line.lstrip()
        if line.startswith("[     0]"):
            filename = line.split("]", 1)[-1].lstrip()
            debug_dir = get_debug_file_directory()
            orig_path = os.path.dirname(library_path).lstrip(os.path.sep)
            return os.path.join(debug_dir, orig_path, filename)

    return None


def read_line_numbers(library_path):
    """Returns a dict mapping symbols to relative paths:lineno.

    In case the passed library does not contain debug symbols or does
    not exists an empty dict is returned.
    """

    symbols = {}

    try:
        data = subprocess.check_output(
            ["nm", "-p", "--line-numbers", library_path],
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        return {}

    for line in data.splitlines():
        parts = line.split()
        if len(parts) == 4:
            type_, symbol, path = parts[1:]
            if type_ == "T":
                symbols[symbol] = os.path.normpath(path)

    if len(symbols) < 2:
        return {}

    # strip away the common path
    assert len(symbols) > 1
    base = symbols.values()[0].split(os.path.sep)
    min_match = len(base)
    for path in symbols.itervalues():
        parts = path.split(os.path.sep)
        same = 0
        for a, b in zip(parts, base):
            if a == b:
                same += 1
            else:
                break
        min_match = min(min_match, same)
    for key, path in symbols.items():
        new_path = os.path.sep.join(path.split(os.path.sep)[min_match - 1:])
        symbols[key] = new_path

    return symbols


def get_abs_library_path(library_name):
    """e.g. returns /usr/lib/x86_64-linux-gnu/libgobject-2.0.so.0 for
    libgobject-2.0.so.0

    FIXME: error handling
    """

    if "LD_LIBRARY_PATH" in os.environ:
        return os.path.join(os.environ["LD_LIBRARY_PATH"], library_name)

    data = subprocess.check_output(["ldconfig", "-p"],
                                   stderr=subprocess.STDOUT)

    for line in data.splitlines():
        line = line.strip()
        parts = line.split(None, 4)
        if len(parts) == 4:
            lib, _, _, path = parts
            if library_name == lib:
                assert os.path.isabs(path)
                return path

    return ""


def get_line_numbers(library_name):
    """Given a shared library returns a dict mapping symbols to relative
    source paths and line numbers.

    In case of an error returns an empty dict.
    """

    # linux only..
    if not sys.platform.startswith("linux"):
        return {}

    library_path = get_abs_library_path(library_name)
    symbols = read_line_numbers(library_path)
    if not symbols:
        library_path = get_debug_file(library_path)
        if library_path is None:
            return {}
        return read_line_numbers(library_path)
    return symbols
