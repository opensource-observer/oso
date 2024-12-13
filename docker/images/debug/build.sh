#!/bin/bash

set -euxo pipefail

mkdir -p /usr/src/app
cd /usr/src/app

curl -sL https://deb.nodesource.com/setup_20.x -o nodesource_setup.sh
bash nodesource_setup.sh

git clone https://github.com/opensource-observer/oso.git
cd oso

poetry install
pnpm install

while true; do sleep 300; done;