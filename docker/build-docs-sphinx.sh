#!/bin/bash

set -e

TAG="ghcr.io/pygobject/pgi-docgen:v4"

sudo docker run --security-opt label=disable \
    --rm  --volume "$(pwd)/..:/home/user/app" \
    -t "${TAG}" pgi-docgen build _docs _docs/_build
