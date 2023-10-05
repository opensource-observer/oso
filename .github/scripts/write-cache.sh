set -euxo pipefail

DOCKER_REPO=${DOCKER_REPO:-ghcr.io/opensource-observer/oso-persistent-cache}
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# A hacky persistent cache for jobs.

cd "${SCRIPT_DIR}/../../"
REPO_DIR=$(pwd)

cd ${CACHE_DIR}

# if the cache file doesn't exist. We should force a new container
if [[ -f "${CACHE_DIR}/.at-cache-load" ]]; then
    # Check if any files have changed. empty directories are ignored
    changes=$(find * -newer "${CACHE_DIR}/.at-cache-load" -type f)

    # If no changes just exit cleanly
    if [[ -z "${changes}" ]]; then
        echo "No changes to cache directory detected. Exiting cleanly"
        exit 0
    fi
fi

cd "${CACHE_DIR}/../"

# Get tag names
latest_tag=${CACHE_PREFIX}-latest
creation_date=${CACHE_PREFIX}-$(date '+%Y-%m-%d %H:%M:%S')
creation_tag=${CACHE_PREFIX}-$(date '+%Y-%m-%d-%H-%M-%S')
today_tag=${CACHE_PREFIX}-$(date '+%Y-%m-%d')
month_tag=${CACHE_PREFIX}-$(date '+%Y-%m')
year_tag=${CACHE_PREFIX}-$(date '+%Y')

CACHE_DIR_NAME="$(basename ${CACHE_DIR})"

# Create the cache using the caching dockerfile
docker build -f "${REPO_DIR}/.github/cache.Dockerfile" \
    --build-arg "CREATION_DATE=${creation_date}" \
    --build-arg "CACHE_DIR_NAME=${CACHE_DIR_NAME}" \
    -t ${DOCKER_REPO}:${latest_tag} \
    -t ${DOCKER_REPO}:${creation_tag} \
    -t ${DOCKER_REPO}:${today_tag} \
    -t ${DOCKER_REPO}:${month_tag} \
    -t ${DOCKER_REPO}:${year_tag} \
    .

# Push all of the tags we just created
docker push -a ${DOCKER_REPO}
