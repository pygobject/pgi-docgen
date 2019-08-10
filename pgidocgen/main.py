#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2017 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import argparse

from . import create, build, stubs, create_debian, update


def main(argv):
    parser = argparse.ArgumentParser(description="pgi-docgen")
    subparser = parser.add_subparsers(title="subcommands")

    create.add_parser(subparser)
    build.add_parser(subparser)
    stubs.add_parser(subparser)
    create_debian.add_parser(subparser)
    update.add_parser(subparser)

    args = parser.parse_args(argv[1:])
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)
