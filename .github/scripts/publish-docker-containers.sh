#!/bin/bash
set -euxo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}/../../"
REPO_DIR=$(pwd)

# Publish all images 
images_to_build="$(find ./docker/images/* -type f -name 'Dockerfile' -exec sh -c 'dirname $0' {} \;)"
tag="$(git rev-parse HEAD)"

for path in $images_to_build; do
    # if directory has an image_name file use that for the image name
    if [ -f "${path}/image_name" ]; then
        image_name=$(cat "${path}/image_name")
    else
        image_name=$(basename "$path")
    fi
    image_dir_name=$(basename "$path")

    image_repo="ghcr.io/opensource-observer/${image_name}"
    sha_image="${image_repo}:${tag}"
    latest_image="${image_repo}:latest"


    echo "Building ${image_name} plugin"
    docker build \
        -t ${sha_image} \
        -t ${latest_image} \
        --label "org.opencontainers.image.source=https://github.com/opensource-observer/oso" \
        --label "observer.opensource.oso.sha=${tag}" \
        --build-arg REPO_SHA=${tag} \
        --build-arg IMAGE_NAME=${image_name} \
        -f docker/images/${image_dir_name}/Dockerfile \
        .
    echo "Publishing the image to ${sha_image}"
    docker push "${sha_image}"
    echo "Publishing latest to ${latest_image}"
    docker push "${latest_image}"
done
