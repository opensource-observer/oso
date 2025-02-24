#!/bin/bash

set -euxo pipefail

cd /usr/src/app

git clone https://github.com/opensource-observer/oso.git
cd oso

uv sync
pnpm install

while true; do sleep 300; done;