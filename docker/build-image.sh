#!/bin/bash

set -e

TAG="ghcr.io/pygobject/pgi-docgen:v4"

sudo docker build \
    --build-arg HOST_USER_ID="$UID" --tag "${TAG}" --file "Dockerfile" ..
