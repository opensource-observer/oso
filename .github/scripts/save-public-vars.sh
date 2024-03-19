#!/bin/bash
set -euo pipefail

# Save public vars into a docker container

DOCKER_REPO=${DOCKER_REPO:-ghcr.io/opensource-observer/oso-public-vars}
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd "${SCRIPT_DIR}/../../"
REPO_DIR=$(pwd)

git_sha=$1
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

pushd "$temp_dir"
mkdir -p "${temp_dir}/public"
output_file="${temp_dir}/public/vars.env"

cat <<EOF >> "${temp_dir}/public/README"
There is a GCP service account in this vars.env file.
This is intentionally done. Please do not file any issues 
regarding this unless you find a specific vulnerability 
with this service account key.

Thanks!
OSO Team @ Kariba Labs
EOF

for var_name in "$@"
do
    # Escape double quotes
    escaped_var=$(echo ${!var_name} | sed s/\"/\"\'\"\'\"/g)
    # We prefix
    echo "PUBLIC_${var_name}=\"${escaped_var}\"" >> $output_file
done

docker build -f "${REPO_DIR}/docker/public-vars.Dockerfile" \
    --build-arg "SHA=${git_sha}" \
    -t ${DOCKER_REPO}:latest \
    .

docker push ${DOCKER_REPO}:latest

popd