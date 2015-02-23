#!/usr/bin/python
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import sys

from pgidocgen.build import main

"""
usage: pgi-docgen-build.py [-h] source

Build the sphinx environ created with pgi-docgen

positional arguments:
  source      path to the sphinx environ base dir
"""

if __name__ == "__main__":
    sys.exit(main(sys.argv))
