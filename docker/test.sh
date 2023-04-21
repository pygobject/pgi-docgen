#!/bin/bash

set -e

TAG="ghcr.io/pygobject/pgi-docgen:v4"

sudo -E docker run -e CODECOV_TOKEN \
    --volume "$(pwd)/..:/home/user/app" --tty "${TAG}" \
    bash -x './docker/test-docker.sh'
