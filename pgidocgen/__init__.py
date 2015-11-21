# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

# Force disable translations for gi libraries.
# For example descriptions of properties/signals are translated.
os.environ["LANG"] = "C.UTF-8"

import pgi
pgi.install_as_gi()
pgi.set_backend("ctypes,null")
