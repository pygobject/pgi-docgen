# -*- coding: utf-8 -*-
# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import importlib

import jinja2

from ..util import escape_rest


_BASEDIR = os.path.dirname(os.path.realpath(__file__))


def get_data_dir():
    return os.path.join(_BASEDIR, "data")


def nolinebreak(text):
    return u" ".join(text.splitlines())


def import_source(name):
    attrs = []
    while name:
        try:
            mod = importlib.import_module(name, __package__)
        except ImportError:
            parts = name.rsplit(".", 1)
            if len(parts) != 2:
                raise
            name = parts[0]
            attrs.append(parts[1])
        else:
            break

    for attr in reversed(attrs):
        mod = getattr(mod, attr)

    return mod


class Loader(jinja2.BaseLoader):

    def get_source(self, environment, template):
        return (import_source(template), None, lambda: True)


_RST_ENV = jinja2.Environment(
    loader=Loader(),
    trim_blocks=True, lstrip_blocks=True, undefined=jinja2.StrictUndefined)
_RST_ENV.filters['erest'] = escape_rest
_RST_ENV.filters['nolinebreak'] = nolinebreak


def get_template(source):
    """Returns a jinja2 rst template"""

    return _RST_ENV.from_string(source)


UTIL = """\
{% macro render_info(info) %}

{{ info.desc }}

{% if info.version_added %}
.. versionadded:: {{ info.version_added|nolinebreak }}
{% endif %}

{% if info.version_deprecated or info.deprecation_desc %}
.. deprecated:: {{ info.version_deprecated|nolinebreak or "???" }}
    {% if info.deprecation_desc %}
    {{ info.deprecation_desc|indent(4, False) }}
    {% endif %}
{% endif %}
{% endmacro %}
"""


class Generator(object):
    """Abstract base class"""

    def is_empty(self):
        """If there is any content to create"""

        raise NotImplementedError

    def write(self, dir_):
        """Create and write everything"""

        raise NotImplementedError

    def get_names(self):
        """A list of names that can be references in
        an rst file (toctree e.g.)
        """

        raise NotImplementedError
