#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
IMAGE='loeper/gradescope-api'
VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./push-docker-image.sh <version>"
    exit 1
fi

docker push "$IMAGE:latest"
docker push "$IMAGE:$VERSION"