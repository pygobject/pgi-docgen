#!/bin/bash

set -e

TAG="ghcr.io/pygobject/pgi-docgen:v4"

sudo docker run --security-opt label=disable \
    --rm  --volume "$(pwd)/..:/home/user/app" \
    -t "${TAG}" uv run pgi-docgen update-debian-info

sudo docker run --security-opt label=disable \
    --rm  --volume "$(pwd)/..:/home/user/app" \
    -t "${TAG}" uv run pgi-docgen create-debian --cachedir /home/user/_debian_build_cache _docs
