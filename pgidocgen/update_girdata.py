# Copyright 2018 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .update import update_doap


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "update-girdata", help="Update the gir data")
    parser.set_defaults(func=main)


def main(args):
    print("Update doap files:")
    update_doap()
