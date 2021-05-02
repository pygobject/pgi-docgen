#!/bin/bash

set -e

TAG="lazka/pgi-docgen:debian-buster"

docker run --security-opt label=disable \
    --rm  --volume "$(pwd)/..:/home/user/app" \
    -t "${TAG}" ./pgi-docgen update-debian-info

docker run --security-opt label=disable \
    --rm  --volume "$(pwd)/..:/home/user/app" \
    -t "${TAG}" ./pgi-docgen create-debian _docs