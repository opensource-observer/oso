#!/bin/bash
set -euo pipefail

# Load public variables from 

DOCKER_REPO=${DOCKER_REPO:-ghcr.io/opensource-observer/oso-public-vars}
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd "${SCRIPT_DIR}/../../"
REPO_DIR=$(pwd)

dest=$1
shift

temp_dir=`mktemp -d`

if [[ ! "$temp_dir" || ! -d "$temp_dir" ]]; then
  echo "Could not create temp dir"
  exit 1
fi

# Delete the temp directory when done
function cleanup {      
  rm -rf "$temp_dir"
  echo "Deleted temp working directory $temp_dir"
}
trap cleanup EXIT

docker pull ghcr.io/opensource-observer/oso-public-vars:latest

# Download the public vars
docker container create --name public-vars ghcr.io/opensource-observer/oso-public-vars:latest /bin/sh

# The /. at the end of the source is important so that it copies the contents of
# the cache directory to the intended destination
docker cp public-vars:/public/. "${temp_dir}"

docker rm public-vars


set_if_not_exists() {
    export $(cat "${temp_dir}/vars.env" | xargs)
    var_name=$1
    dest=$2
    public_var_name="PUBLIC_${var_name}"

    set +u
    if [[ ! -z "${!var_name}" ]]; then
        echo "Variable '$var_name' exists"
    else
        echo "Variable '$var_name' does not exist. Loading from ${public_var_name}"
        echo "${var_name}=${!public_var_name}" >> "${dest}"
    fi
    set -u
}

for var_name in "$@"
do
    set_if_not_exists "${var_name}" "${dest}"
done
