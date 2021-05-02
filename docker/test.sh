#!/bin/bash

set -e

TAG="lazka/pgi-docgen:debian-buster"

sudo -E docker run -e CODECOV_TOKEN \
    --volume "$(pwd)/..:/home/user/app" --tty "${TAG}" \
    bash -x './docker/test-docker.sh'
