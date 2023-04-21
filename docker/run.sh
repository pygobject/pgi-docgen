#!/bin/bash

set -e

TAG="ghcr.io/pygobject/pgi-docgen:v4"

sudo docker run --security-opt label=disable \
    --rm  --volume "$(pwd)/..:/home/user/app" \
    --tty --interactive "${TAG}" bash
