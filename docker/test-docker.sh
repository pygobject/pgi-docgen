#!/bin/bash

set -e

export XDG_DATA_DIRS="/home/user/_debian_build_cache:$XDG_DATA_DIRS"

sudo chown -R "$(whoami)" .
poetry install
poetry run pytest tests --cov --cov-branch --cov-report=xml
bash <(curl -s https://codecov.io/bash)
poetry run flake8
