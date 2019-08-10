#!/bin/bash

set -e

export XDG_DATA_DIRS="$PGI_DOCGEN_DEBIAN_DATA_DIR:$XDG_DATA_DIRS"

sudo chown -R "$(whoami)" .
python3 -m pytest tests --cov --cov-branch --cov-report=xml
bash <(curl -s https://codecov.io/bash)
python3 -m flake8
