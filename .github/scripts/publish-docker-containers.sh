#!/bin/bash
set -euxo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}/../../"
REPO_DIR=$(pwd)

# Publish all images 
images_to_build="$(find ./docker/images/* -type f -name 'Dockerfile' -exec sh -c 'dirname $0' {} \;)"
immutable_tag="$(git rev-parse HEAD)"
if [[ `git status --porcelain` ]]; then
  immutable_tag="build-$(date +%s)"
fi

# By default, the target tag is the latest
target_tag="${1:-latest}"


for path in $images_to_build; do
    # if directory has an image_name file use that for the image name
    if [ -f "${path}/image_name" ]; then
        image_name=$(cat "${path}/image_name")
    else
        image_name=$(basename "$path")
    fi
    image_dir_name=$(basename "$path")

    image_repo="ghcr.io/opensource-observer/${image_name}"
    sha_image="${image_repo}:${immutable_tag}"
    target_image="${image_repo}:${target_tag}"


    echo "Building ${image_name} image"
    docker build \
        -t ${sha_image} \
        -t ${target_image} \
        --label "org.opencontainers.image.source=https://github.com/opensource-observer/oso" \
        --label "observer.opensource.oso.sha=${immutable_tag}" \
        --build-arg REPO_SHA=${immutable_tag} \
        --build-arg IMAGE_NAME=${image_name} \
        -f docker/images/${image_dir_name}/Dockerfile \
        .
    echo "Publishing the image to ${sha_image}"
    docker push "${sha_image}"
    echo "Publishing ${target_tag} to ${target_image}"
    docker push "${target_image}"
done
