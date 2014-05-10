#!/bin/sh
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# Example usage: "./build.sh Atk-1.0"
# Result can be found in "_docs/_build"

set -e

export PGI_CACHE=$(mktemp)

for mod in "$@"
do
    echo "#####################################"
    echo "# $mod"
    python ./pgi-docgen.py _docs _docs/_build "$mod" 
done

rm -f "$PGI_CACHE"

python ./pgi-docgen-build.py _docs
