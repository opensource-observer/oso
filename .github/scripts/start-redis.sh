#!/bin/bash
set -uxo pipefail

cache_dump_path="${CACHE_DIR}/redis/dump.rdb"
dump_path="/redis/dump.rdb"

# Ensure we have the redis tools
sudo apt-get install -y redis-tools

mkdir -p "/redis"

if [ -f "${cache_dump_path}" ]; then
    cp "${cache_dump_path}" "${dump_path}"
fi

# Start the redis container
start_redis() {
    docker run --name redis -d -p 6379:6379 -v /redis:/data redis redis-server --save 60 1000 --loglevel warning
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
        stop_redis
        # Clear the cache and also the current dump if the dump is corrupted
        if [ -f "${cache_dump_path}" ]; then
            rm "${cache_dump_path}"
        fi

        if [ -f "${dump_path}" ]; then
            rm "${dump_path}"
        fi
        
        stop_redis
        start_redis
    fi
    sleep 5 
done;
exit 1
