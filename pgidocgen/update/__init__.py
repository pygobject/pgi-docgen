# Copyright 2018 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .doap import add_parser as add_parser_doap
from .debian_info import add_parser as add_parser_debian
from .docref import add_parser as add_parser_docref
from .clsimages import add_parser as add_parser_clsimages
from .clsimages4 import add_parser as add_parser_clsimages4


def add_parser(subparser):
    add_parser_doap(subparser)
    add_parser_debian(subparser)
    add_parser_docref(subparser)
    add_parser_clsimages(subparser)
    add_parser_clsimages4(subparser)
