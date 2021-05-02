#!/bin/bash

set -e

TAG="lazka/pgi-docgen:v3"

docker run --security-opt label=disable \
    --rm  --volume "$(pwd)/..:/home/user/app" \
    -t "${TAG}" ./pgi-docgen build _docs _docs/_build