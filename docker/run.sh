#!/bin/bash

set -e

TAG="lazka/pgi-docgen:debian-buster"

docker run --security-opt label=disable \
    --rm  --volume "$(pwd)/..:/home/user/app" \
    --tty --interactive "${TAG}" bash
