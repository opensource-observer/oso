#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}/../../"
REPO_DIR=$(pwd)

# For now if a plugin has both a pyproject.toml and a package.json. The python
# will be used by nature of the order of docker image publishing
python_plugins="$(find ./warehouse/cloudquery-* -type f -name 'pyproject.toml' -exec sh -c 'dirname $0' {} \;)"
ts_plugins="$(find ./warehouse/cloudquery-* -type f -name 'package.json' -exec sh -c 'dirname $0' {} \;)"
tag="$(git rev-parse HEAD)"

build_base_image() {
    language="$1"
    tag="$2"
    base_image="ghcr.io/opensource-observer/${language}-base:${tag}"
    dockerfile_path="./docker/cloudquery/${language}-base.Dockerfile"
    docker build -t "${base_image}" -f "${dockerfile_path}" .
    echo $base_image
}

# Build the base images
py_base_image=$(build_base_image py $tag)
ts_base_image=$(build_base_image ts $tag)
prefix="cloudquery-"

for path in $ts_plugins; do
    plugin_name=$(basename $path)
    # Remove the cloudquery prefix
    plugin_name=${plugin_name#"$prefix"}

    plugin_image="ghcr.io/opensource-observer/cloudquery-${plugin_name}:${tag}"

    echo "Building ${plugin_name} plugin"
    docker build -t ${plugin_image} \
        --build-arg PLUGIN_NAME=${plugin_name} \
        --build-arg BASE_IMAGE=${ts_base_image} \
        -f docker/cloudquery/ts.Dockerfile \
        .
    echo "Publishing the plugin to ${plugin_image}"
    docker push ${plugin_image}
done

for path in $python_plugins; do
    plugin_name=$(basename $path)
    # Remove the cloudquery prefix
    plugin_name=${plugin_name#"$prefix"}

    plugin_cmd=$(echo $plugin_name | sed "s/-/_/g")
    plugin_image="ghcr.io/opensource-observer/cloudquery-${plugin_name}:${tag}"

    # Skip the example
    if [[ $plugin_name = "example_plugin" ]]; then
        continue
    fi
    echo "Building ${plugin_name} plugin"

    docker build -t ${plugin_image} \
        --build-arg PLUGIN_NAME=${plugin_name} \
        --build-arg PLUGIN_CMD=${plugin_cmd} \
        --build-arg BASE_IMAGE=${ts_base_image} \
        -f docker/cloudquery/py.Dockerfile \
        .

    echo "Publishing the plugin to ${plugin_image}"
    docker push ${plugin_image}
done