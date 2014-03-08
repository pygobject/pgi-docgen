#/bin/bash

# This sets up a virtual python environment and installs all dependencies
# into "_venv". If this directory exists it will only start the virtual env.
# Afterwards use build.sh for example

echo "Usage: 'source bootstrap.sh'"

VENV="_venv"

if [ -d "$VENV" ]; then
    . "$VENV"/bin/activate
else
    virtualenv _venv
    . "$VENV"/bin/activate
    pip install git+https://github.com/lazka/pgi.git
    pip install sphinx
    pip install BeautifulSoup
fi
