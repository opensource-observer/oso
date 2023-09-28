#!/bin/bash

cd /usr/src/app/indexer
node --version
sleep 3
pnpm migration:run
NO_DYNAMIC_LOADS=true pnpm test -- --verbose=true 