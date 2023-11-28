#!/bin/bash
set -uxo pipefail

redis-cli save

docker kill redis