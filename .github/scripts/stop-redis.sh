#!/bin/bash
set -uxo pipefail

redis-cli --rdb "${CACHE_DIR}/redis/dump.rdb"

docker kill redis