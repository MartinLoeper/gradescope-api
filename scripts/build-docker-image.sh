#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
IMAGE='loeper/gradescope-api'
VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./build-docker-image.sh <version>"
    exit 1
fi

docker buildx build -t "$IMAGE:latest" -t "$IMAGE:$VERSION" -f ".devcontainer/Dockerfile.prod" --load "$SCRIPT_DIR/.."