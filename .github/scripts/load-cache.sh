set -euxo pipefail

# Ensure the cache directory exists
mkdir -p ${CACHE_DIR}

# Currently only loads the latest cache
echo "Attempting to load docker cache into ${CACHE_DIR}"

# We need to create a container just so we can do the docker cp
docker container create --name cache ghcr.io/hypercerts-org/oso-persistent-cache:${CACHE_PREFIX}-latest /bin/sh

# The /. at the end of the source is important so that it copies the contents of
# the cache directory to the intended destination
docker cp cache:/cache/. ${CACHE_DIR}

# Touch a file to use for checking for changed files in the cache directory
touch "${CACHE_DIR}/.at-cache-load"