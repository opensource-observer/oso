#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}/../../"
REPO_DIR=$(pwd)

cd ${REPO_DIR}/indexer

export NODE_OPTIONS=--max-old-space-size=6144
export GITHUB_TOKEN=${X_GITHUB_TOKEN}

pnpm --stack-size=2000 start --cache-dir "${CACHE_DIR}" --run-dir "${RUN_DIR}" scheduler "$@" 2>&1 | tee "${LOG_FILE}"
