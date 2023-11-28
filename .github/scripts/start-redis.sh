#!/bin/bash
set -uxo pipefail

# Ensure we have the redis tools
sudo apt-get install -y redis-tools

mkdir -p "${CACHE_DIR}/redis"

# Start the redis container
docker run --name redis -p 6379:6379 -d -v "${CACHE_DIR}/redis:/data" redis redis-server --save 60 1000 --loglevel warning

retries=0
max_retries=30
until [ "$retries" -ge "$max_retries" ]
do
    redis-cli ping && break && exit 0
    retries=$((retries+1))
    sleep 5 
done;
exit 1