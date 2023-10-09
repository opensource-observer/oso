#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}/../../"
REPO_DIR=$(pwd)

cd ${REPO_DIR}/indexer

pnpm start --cache-dir "${CACHE_DIR}" --run-dir "${RUN_DIR}" scheduler "$@" 2>&1 | tee "${LOG_FILE}"