#!/usr/bin/python
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""
usage: pgi-docgen-build.py [-h] [--devhelp] source target

Build the sphinx environ created with pgi-docgen

positional arguments:
  source      path to the sphinx environ base dir
  target      path to where the resulting build should be

optional arguments:
  -h, --help  show this help message and exit
  --devhelp
"""

import sys

from pgidocgen.build import main


if __name__ == "__main__":
    sys.exit(main(sys.argv))
