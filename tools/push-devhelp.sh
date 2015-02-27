#!/bin/sh
# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

cd _devhelp/_build
rm -f README.rst
echo "This repository was created automatically using https://github.com/lazka/pgi-docgen\n" >> README.rst
echo "It contains devhelp packages for PyGObject\n\n" >> README.rst
echo "1) git clone https://github.com/lazka/pgi-docs-devhelp.git ~/.local/share/devhelp/books\n" >> README.rst
echo "2) devhelp\n" >> README.rst
echo "To update:\n" >> README.rst
echo "1) cd ~/.local/share/devhelp/books\n" >> README.rst
echo "2) git fetch --all\n" >> README.rst
echo "3) git reset --hard origin/master\n" >> README.rst
rm -rf .?*
git init
git add .
git commit -m "update"
git remote add origin https://github.com/lazka/pgi-docs-devhelp.git
git push --set-upstream origin master --force
