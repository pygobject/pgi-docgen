#!/bin/bash

set -e

TAG="lazka/pgi-docgen:debian-buster"

docker build \
    --build-arg HOST_USER_ID="$UID" --build-arg "http_proxy=$http_proxy" --tag "${TAG}" --file "Dockerfile" ..