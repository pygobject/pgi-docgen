#!/bin/bash

set -e

virtualenv --python=/usr/bin/python3.6 /tmp/venv
source /tmp/venv/bin/activate

pip install git+https://github.com/pygobject/pgi.git
pip install pytest cairocffi docutils jinja2 beautifulsoup4 lxml sphinx

python -m pytest tests
