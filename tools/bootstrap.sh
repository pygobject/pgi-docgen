#/bin/bash

# This sets up a virtual python environment and installs all dependencies
# into "_venv". If this directory exists it will only start the virtual env.
# Afterwards use build.sh for example

echo "Usage: 'source bootstrap.sh'"

VENV="${VENV:-_venv}"
PYTHON=${PYTHON:-python3}

if [ -d "$VENV" ]; then
    . "$VENV"/bin/activate
else
    virtualenv --system-site-packages -p $PYTHON "$VENV"
    . "$VENV"/bin/activate
    pip install git+https://github.com/pygobject/pgi.git
    pip install sphinx
    pip install beautifulsoup4
    pip install jinja2
    pip install cairocffi
fi
