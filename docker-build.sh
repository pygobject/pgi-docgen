#!/bin/bash

set -e
set -x

cd docker

./build-image.sh

./build-docs.sh
ls -ld ../_docs

./build-docs-sphinx.sh
ls -1 ../_docs/_build