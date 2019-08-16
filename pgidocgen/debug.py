# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import sys
import bisect
import subprocess

"""
Provides source paths and line numbers for shared libraries.
The library has to include debug symbols or a separate debug symbol file has
to be present (same requirements as for gdb to display line numbers)

Check out get_line_numbers_for_name()
"""


def get_debug_file_directory():
    """Returns the directory where separate debug symbols can be found

    TODO: Don't hard code this? See "show debug-file-directory" in gdb
    """

    return "/usr/lib/debug"


def get_debug_link_file(library_path):
    """Returns the path of the linked debug library or None"""

    library_path = os.path.abspath(library_path)
    data = read_elf_section(library_path, ".gnu_debuglink")
    if not data:
        return None
    filename = data.split(b"\x00", 1)[0].decode("ascii")
    debug_dir = get_debug_file_directory()
    orig_path = os.path.dirname(library_path).lstrip(os.path.sep)
    return os.path.join(debug_dir, orig_path, filename)


def read_elf_section(library_path, name):
    try:
        data = subprocess.check_output(["readelf", "-x", name,
                                        library_path],
                                       stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        return b""

    def tobin(s):
        d = b""
        for i in range(0, len(s), 2):
            d += bytes([int(s[i:i + 2].decode("ascii"), 16)])
        return d

    content = b""
    for line in data.splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2 or not parts[0].startswith(b"0x"):
            continue
        content += parts[1][:35].replace(b" ", b"")
    return tobin(content)


def get_debug_build_id(library_path):
    """Returns the build id for the library path or None"""

    data = read_elf_section(library_path, ".note.gnu.build-id")
    if not data:
        return None
    index = data.find(b"GNU")
    assert index != -1
    index += 4
    return "".join(["%02x" % c for c in bytearray(data[index:])])


def get_debug_build_id_for_name(library_name):
    """Returns the build id for the library name or None"""
    if not sys.platform.startswith("linux"):
        return None
    library_path = get_abs_library_path(library_name)
    return get_debug_build_id(library_path)


def get_debug_build_id_file(library_path):
    """Returns the path of the linked debug library or None"""

    id_ = get_debug_build_id(library_path)
    if id_ is None:
        return None
    debug_dir = get_debug_file_directory()
    return os.path.join(debug_dir, ".build-id", id_[:2], id_[2:] + ".debug")


def get_debug_files(library_path):
    """Returns the possible paths of the linked debug library"""

    # See https://sourceware.org/gdb/onlinedocs/gdb/Separate-Debug-Files.html
    paths = [library_path]

    path = get_debug_link_file(library_path)
    if path is not None:
        paths.append(path)

    path = get_debug_build_id_file(library_path)
    if path is not None:
        paths.append(path)

    return paths


def get_debug_files_for_name(library_name):

    # linux only..
    if not sys.platform.startswith("linux"):
        return []

    library_path = get_abs_library_path(library_name)
    return get_debug_files(library_path)


def get_public_symbols(library_path):
    try:
        data = subprocess.check_output(
            ["objdump", "-t", "-j", ".text", library_path],
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        return {}

    symbols = {}
    for line in data.decode("utf-8").splitlines():
        parts = line.split(None, 1)
        if not parts:
            continue
        try:
            addr = int(parts[0], 16)
        except ValueError:
            continue
        if parts[1][0] not in "ug":
            continue
        symbols[addr] = line.split()[-1]
    return symbols


def get_compile_units(library_path):
    try:
        data = subprocess.check_output(
            ["objdump", "--dwarf=info", library_path],
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        return {}

    cus = {}

    cu_name = None
    cu_dir = None
    cu_low_pc = None
    type_ = None
    for line in data.decode("utf-8", "surrogateescape").splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        if parts[1] == "Abbrev":
            type_ = parts[-1].strip("()")
            cu_name = cu_dir = cu_low_pc = None
            continue

        if type_ == "DW_TAG_compile_unit":
            new = True
            if parts[1] == "DW_AT_name":
                cu_name = parts[-1]
            elif parts[1] == "DW_AT_comp_dir":
                cu_dir = parts[-1]
            elif parts[1] == "DW_AT_low_pc":
                cu_low_pc = parts[-1]
            else:
                new = False

            if new and cu_name and cu_dir and cu_low_pc:
                cus[int(cu_low_pc, 16)] = \
                    os.path.normpath(os.path.join(cu_dir, cu_name))

    return cus


def get_lines(library_path):
    try:
        data = subprocess.check_output(
            ["objdump", "--dwarf=decodedline", library_path],
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        return {}

    lines = {}
    for line in data.splitlines():
        parts = line.split()
        if len(parts) != 3:
            continue
        try:
            addr = int(parts[-1], 16)
        except ValueError:
            continue
        lines[addr] = str(int(parts[1]) - 1)

    return lines


def get_line_numbers_for_file(library_path):
    """Returns a dict mapping symbols to relative paths:lineno.

    In case the passed library does not contain debug symbols or does
    not exists an empty dict is returned.

    Requires objdump.
    """

    cus = get_compile_units(library_path)
    cu_index = sorted(cus.keys())

    def find_nearest_cu(addr):
        i = bisect.bisect_right(cu_index, addr)
        if i:
            return cus[cu_index[i - 1]]
        raise ValueError

    lines = get_lines(library_path)
    line_index = sorted(lines.keys())

    def find_nearest_line(addr):
        i = bisect.bisect_right(line_index, addr)
        if i:
            return lines[line_index[i - 1]]
        raise ValueError

    public = get_public_symbols(library_path)
    symbols = {}
    for addr, symbol in sorted(public.items()):
        cu, line = find_nearest_cu(addr), find_nearest_line(addr)
        if symbol not in symbols:
            symbols[symbol] = "%s:%s" % (cu, line)

    if len(symbols) < 2:
        return {}

    # strip away the common path
    assert len(symbols) > 1
    base = sorted(symbols.values(), key=len)[0].split(os.path.sep)
    min_match = len(base)
    for symbol, path in symbols.items():
        parts = path.split(os.path.sep)
        same = 0
        for a, b in zip(parts, base):
            if a == b:
                same += 1
            else:
                break
        min_match = min(min_match, same)

    # we want at least one directory (it's uncommon that the source is in /)
    if min_match >= len(base) - 1:
        min_match = len(base) - 2

    for symbol, path in symbols.items():
        new_path = os.path.sep.join(path.split(os.path.sep)[min_match:])
        symbols[symbol] = new_path

    return symbols


def get_abs_library_path(library_name):
    """e.g. returns /usr/lib/x86_64-linux-gnu/libgobject-2.0.so.0 for
    libgobject-2.0.so.0
    """

    if "LD_LIBRARY_PATH" in os.environ:
        path = os.path.join(os.environ["LD_LIBRARY_PATH"], library_name)
        path = os.path.abs(path)
        if not os.path.exists(path):
            raise LookupError(library_name)
        return path

    # On debian ldconfig is in /sbin which isn't in PATH by default
    env = os.environ.copy()
    paths = [p for p in env.get("PATH", "").split(os.pathsep)]
    paths.append("/sbin")
    env["PATH"] = os.pathsep.join(paths)

    data = subprocess.check_output(["ldconfig", "-p"],
                                   stderr=subprocess.STDOUT, env=env)

    for line in data.decode("utf-8").splitlines():
        line = line.strip()
        parts = line.split(None, 4)
        if len(parts) == 4:
            lib, _, _, path = parts
            if library_name == lib:
                assert os.path.isabs(path)
                return path

    raise LookupError(library_name)


def get_line_numbers_for_name(library_name):
    """Given a shared library returns a dict mapping symbols to relative
    source paths and line numbers.

    In case of an error returns an empty dict.
    """

    for path in get_debug_files_for_name(library_name):
        symbols = get_line_numbers_for_file(path)
        if symbols:
            return symbols
    return {}
