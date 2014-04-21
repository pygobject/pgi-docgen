#!/bin/sh
# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# Example usage: "./build.sh Atk-1.0"
# Result can be found in "_devhelp/_build"

set -e

for mod in "$@"
do
    echo "#####################################"
    echo "# $mod"
    python ./pgi-docgen.py --devhelp _devhelp _devhelp/_build "$mod"
done

python ./pgi-docgen-build.py _devhelp
