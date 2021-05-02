#!/bin/bash

set -e

TAG="lazka/pgi-docgen:v3"

docker build \
    --build-arg HOST_USER_ID="$UID" --build-arg "http_proxy=$http_proxy" --tag "${TAG}" --file "Dockerfile" ..