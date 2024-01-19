#!/bin/bash
# Builds a ts connector into a docker container and pushes it to github packages.
# 
# Usage:
# deploy-connector.sh {connector_source_name} {docker_image_version}
set -euxo pipefail

connector_source_name=$1
docker_image_name=${connector_source_name}-airbyte-connector
docker_image_version=$2

DOCKER_REPO=${DOCKER_REPO:-ghcr.io/opensource-observer/${docker_image_name}}
docker_tag="${DOCKER_REPO}:${docker_image_version}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Go to the root
cd "${SCRIPT_DIR}/../"

docker build --build-arg SOURCE_DIR="connectors/${connector_source_name}" -t "${docker_tag}" -f ./docker/ts-connector.Dockerfile . 
docker push "${docker_tag}"