#!/bin/sh
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# after ./build_all.sh, call this to force push the build to github pages

cd _docs/_build
rm -f README.rst
echo "This repository was created automatically using https://github.com/lazka/pgi-docgen\n" >> README.rst
echo "It contains a static website which can be viewed at http://lazka.github.io/pgi-docs/\n" >> README.rst
echo "It also works offline: http://github.com/lazka/pgi-docs/archive/gh-pages.zip" >> README.rst
rm -rf .?*
git init
git checkout -b gh-pages
touch  .nojekyll
git add .
git commit -m "update"
git remote add origin https://github.com/lazka/pgi-docs.git
git push --force --set-upstream origin gh-pages
