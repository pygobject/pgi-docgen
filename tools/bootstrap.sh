#/bin/bash

# This sets up a virtual python environment and installs all dependencies
# into "_venv". If this directory exists it will only start the virtual env.
# Afterwards use build.sh for example

echo "Usage: 'source bootstrap.sh'"

VENV="_venv"
PYTHON=${PYTHON:-python2}

if [ -d "$VENV" ]; then
    . "$VENV"/bin/activate
else
    virtualenv --system-site-packages -p $PYTHON _venv
    . "$VENV"/bin/activate
    pip install git+https://github.com/lazka/pgi.git
    pip install sphinx
    pip install BeautifulSoup
    pip install jinja2
    pip install cairocffi
fi
