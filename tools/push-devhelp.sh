#!/bin/sh
# Copyright 2014, 2016 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

set -e

DIR="$( cd "$( dirname "$0" )" && pwd )"
BUILD="$DIR/../_docs/_build_devhelp"

rm -rf _temp
git clone https://github.com/pygobject/pgi-docs-devhelp.git _temp
cd _temp

git rm -r "*";
cp -r "$BUILD"/* .

# add readme
echo "This repository was created automatically using https://github.com/pygobject/pgi-docgen\n" >> README.rst
echo "It contains devhelp packages for PyGObject\n\n" >> README.rst
echo "1) git clone https://github.com/pygobject/pgi-docs-devhelp.git ~/.local/share/devhelp/books\n" >> README.rst
echo "2) devhelp\n" >> README.rst
echo "To update:\n" >> README.rst
echo "1) cd ~/.local/share/devhelp/books\n" >> README.rst
echo "2) git pull\n" >> README.rst

git add .
git commit -m "update"
git push
