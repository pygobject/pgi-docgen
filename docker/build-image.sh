#!/bin/bash

set -e

TAG="lazka/pgi-docgen"

sudo docker build \
    --build-arg HOST_USER_ID="$UID" --tag "${TAG}" --file "Dockerfile" ..
