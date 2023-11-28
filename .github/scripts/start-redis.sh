#!/bin/bash
set -uxo pipefail

# Ensure we have the redis tools
sudo apt-get install -y redis-tools

mkdir -p "${CACHE_DIR}/redis"

ls -halt "${CACHE_DIR}/redis"

# Start the redis container
start_redis() {
    docker run --name redis -d -p 6379:6379 -v "${CACHE_DIR}/redis:/data" redis redis-server --save 60 1000 --loglevel warning
}

stop_redis() {
    docker kill redis || true
}

start_redis

retries=0
max_retries=60
until [ "$retries" -ge "$max_retries" ]
do
    redis-cli ping && break && exit 0
    retries=$((retries+1))
    if [ "$retries" -eq 30 ]; then
        rm -r "${CACHE_DIR}/redis"
        mkdir -p "${CACHE_DIR}/redis"
        
        stop_redis
        start_redis
    fi
    sleep 5 
done;
exit 1
