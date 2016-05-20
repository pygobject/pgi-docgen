# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""Database containing additional optional info about common gir files.

The gir files don't contain all the info we would like to have so this is a
collection of various information about the relation of the girs and their
projects and additional data fetched from other sources.

See tools/fetch-*.py for scripts which updates some of this info from external
sources.
"""

import os
import json

from .doap import get_project_summary, get_doap_dir, get_doap_path
from .project import Project, PROJECTS
from .library import Library


get_project_summary, get_doap_dir, get_doap_path, Project, Library, PROJECTS

_BASEDIR = os.path.dirname(os.path.realpath(__file__))


def get_debian_path():
    return os.path.join(_BASEDIR, "debian-packages.json")


def get_class_image_dir(namespace, version):
    """The image directory for a given `namespace` and `version`.

    The returned directory path might not exist.
    """

    return os.path.join(
            _BASEDIR, "clsimages",
            "%s-%s" % (namespace, version))


def get_class_image_path(namespace, version, class_name):
    """Returns an absolute path to the class image file.

    Might not exist.
    """

    return os.path.join(get_class_image_dir(namespace, version),
                        "%s.png" % class_name)


def get_docref_dir():
    """The gtk-doc reference mapping directory"""

    return os.path.join(_BASEDIR, "docref")


def get_docref_path(namespace, version):
    """Returns the path to a json file containing a mapping of Python
    identifiers to URL for gtk-doc online instances.

    Returned path might not exist.
    """

    return os.path.join(get_docref_dir(), "%s-%s.json" % (namespace, version))


def load_doc_references(namespace, version):
    """Returns a mapping of gtk-doc references to URLs or an empty dict
    on error.
    """

    path = get_docref_path(namespace, version)
    try:
        with open(path, "rb") as h:
            return json.load(h)
    except IOError:
        return {}
