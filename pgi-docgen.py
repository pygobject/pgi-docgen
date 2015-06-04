#!/usr/bin/python
# Copyright 2013, 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""
usage: pgi-docgen.py [-h] target namespace [namespace ...]

Create a sphinx environ

positional arguments:
  target      path to where the resulting source should be
  namespace   namespace including version e.g. Gtk-3.0

optional arguments:
  -h, --help  show this help message and exit
"""

import sys

from pgidocgen.create import main

if __name__ == "__main__":
    sys.exit(main(sys.argv))
