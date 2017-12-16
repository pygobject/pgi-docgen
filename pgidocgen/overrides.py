# -*- coding: utf-8 -*-
# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from sphinx.pycode import ModuleAnalyzer
from sphinx.errors import PycodeError

from .util import import_namespace


def parse_override_docs(namespace, version):
    import_namespace(namespace, version)

    try:
        ma = ModuleAnalyzer.for_module("pgi.overrides.%s" % namespace)
    except PycodeError:
        return {}
    docs = {}
    for key, value in ma.find_attr_docs().items():
        docs[namespace + "." + ".".join(filter(None, key))] = "\n".join(value)
    return docs
