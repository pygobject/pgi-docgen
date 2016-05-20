# Copyright 2016 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import json


_BASEDIR = os.path.dirname(os.path.realpath(__file__))


def get_doap_dir():
    return os.path.join(_BASEDIR, "doap")


def get_doap_path(namespace):
    """Returns an absolute path to the doap file of a project.

    Might not exist.
    """

    return os.path.join(get_doap_dir(), "%s.doap" % namespace)


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


def load_debian():
    """Returns a mapping of namespace-version to debian related info"""

    path = get_debian_path()
    try:
        with open(path, "rb") as h:
            return json.load(h)
    except IOError:
        return {}
