#!/bin/sh
# Copyright 2013, 2016 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# after ./build-debian.py, call this to force push the build to github pages

set -e

DIR="$( cd "$( dirname "$0" )" && pwd )"
BUILD="$DIR/../_docs/_build"

rm -rf _temp
git clone https://github.com/lazka/pgi-docs.git _temp
cd _temp
git checkout gh-pages

git rm -r "*";
cp -r "$BUILD"/* .

# add readme
echo "This repository was created automatically using https://github.com/lazka/pgi-docgen\n" >> README.rst
echo "It contains a static website which can be viewed at http://lazka.github.io/pgi-docs/\n" >> README.rst
echo "It also works offline: http://github.com/lazka/pgi-docs/archive/gh-pages.zip" >> README.rst

# disable jekyll
touch  .nojekyll

git add .
git commit -m "update"
git push
