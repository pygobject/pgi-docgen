#!/bin/bash
# Copyright 2013, 2016, 2017 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

set -e

DIR="$( cd "$( dirname "$0" )" && pwd )"
BUILD="$DIR/../_docs/_build"

if [ -d "$BUILD" ]; then
    TEMP_BUILD="$DIR/_temp_build"
    rm -rf "$TEMP_BUILD"
    git clone git@github.com:lazka/pgi-docs.git "$TEMP_BUILD" || git clone https://github.com/lazka/pgi-docs.git "$TEMP_BUILD"
    cd "$TEMP_BUILD"
    git checkout master

    git rm -r "*";
    cp -r "$BUILD"/* .

    # add readme
    echo -e 'This repository was created automatically using https://github.com/pygobject/pgi-docgen\n' >> README.rst
    echo -e 'It contains a static website which can be viewed at https://lazka.github.io/pgi-docs/\n' >> README.rst
    echo -e 'It also works offline: https://github.com/lazka/pgi-docs/archive/refs/heads/master.zip' >> README.rst

    # disable jekyll
    touch  .nojekyll

    git add .
    git commit -m "update" || true
    git push
fi

DEVHELPBUILD="$DIR/../_docs/_build_devhelp"

if [ -d "$DEVHELPBUILD" ]; then
    TEMP_DEVHELP="$DIR/_temp_devhelp"
    rm -rf "$TEMP_DEVHELP"
    git clone https://github.com/pygobject/pgi-docs-devhelp.git "$TEMP_DEVHELP"
    cd "$TEMP_DEVHELP"

    git rm -r "*";
    cp -r "$DEVHELPBUILD"/* .

    # add readme
    echo -e 'This repository was created automatically using https://github.com/pygobject/pgi-docgen\n' >> README.rst
    echo -e 'It contains devhelp packages for PyGObject\n\n' >> README.rst
    echo -e '1) git clone https://github.com/pygobject/pgi-docs-devhelp.git ~/.local/share/devhelp/books\n' >> README.rst
    echo -e '2) devhelp\n' >> README.rst
    echo -e 'To update:\n' >> README.rst
    echo -e '1) cd ~/.local/share/devhelp/books\n' >> README.rst
    echo -e '2) git pull\n' >> README.rst

    git add .
    git commit -m "update" || true
    git push
fi
