#!/bin/bash

set -e

DIR="$( cd "$( dirname "$0" )" && pwd )"
DOCKERFILE="$DIR/Dockerfile"
DOCKERIMAGE="testimage"
CACHEDIR="$DIR/_ci_cache"

if [ ! -f "$CACHEDIR/$DOCKERIMAGE" ]; then
    docker build -t "$DOCKERIMAGE" -f "$DOCKERFILE" .
    mkdir -p "$CACHEDIR";
    docker image save "$DOCKERIMAGE" -o "$CACHEDIR/$DOCKERIMAGE";
fi;

docker image load -i "$CACHEDIR/$DOCKERIMAGE"
docker run --volume "$(pwd):/app" --workdir "/app" --tty --detach "$DOCKERIMAGE" bash > container_id
docker exec "$(cat container_id)" bash -x ".circleci/test-docker.sh"
docker stop "$(cat container_id)"
