# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import re
import keyword


def escape_keyword(text, reg=re.compile("^(%s)$" % "|".join(keyword.kwlist))):
    return reg.sub(r"\1_", text)


def merge_in_overrides(obj):
    # hide overrides by merging the bases in
    possible_bases = []
    for base in obj.__bases__:
        if base.__name__ == obj.__name__ and base.__module__ == obj.__module__:
            for upper_base in base.__bases__:
                possible_bases.append(upper_base)
        else:
            possible_bases.append(base)

    # preserve the mro
    mro_bases = []
    for base in obj.__mro__:
        if base in possible_bases:
            mro_bases.append(base)
    return mro_bases


def method_is_static(obj):
    try:
        return obj.im_self is not None
    except AttributeError:
        return True


def make_rest_title(text, char="="):
    return text + "\n" + len(text) * char


def get_gir_dirs():
    if "XDG_DATA_DIRS" in os.environ:
        dirs = os.environ["XDG_DATA_DIRS"].split(os.pathsep)
    else:
        dirs = ["/usr/local/share/", "/usr/share/"]

    return [os.path.join(d, "gir-1.0") for d in dirs]


class Generator(object):
    """Abstract base class"""

    def is_empty(self):
        """If there is any content to create"""
        raise NotImplementedError

    def write(self):
        """Create and write everything"""
        raise NotImplementedError

    def get_name(self):
        """A name that can be references in an rst file (toctree e.g.)"""
        raise NotImplementedError
