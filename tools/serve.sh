#!/bin/bash

set -e

DIR="$( cd "$( dirname "$0" )" && pwd )"
BUILD="$DIR/../_docs/_build"

python -m http.server -b 127.0.0.1 -d "$BUILD"
