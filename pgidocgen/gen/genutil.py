# -*- coding: utf-8 -*-
# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import jinja2


_RST_ENV = jinja2.Environment(
    trim_blocks=True, lstrip_blocks=True, undefined=jinja2.StrictUndefined)


def get_template(source):
    """Returns a jinja2 rst template"""

    return _RST_ENV.from_string(source)


class Generator(object):
    """Abstract base class"""

    def is_empty(self):
        """If there is any content to create"""

        raise NotImplementedError

    def write(self, dir_, module_fileobj=None):
        """Create and write everything"""

        raise NotImplementedError

    def get_names(self):
        """A list of names that can be references in
        an rst file (toctree e.g.)
        """

        raise NotImplementedError
