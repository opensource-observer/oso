#!/bin/bash

cd /usr/src/app/indexer
node --version
pnpm migration:run
NO_DYNAMIC_LOADS=true pnpm test -- --verbose=true 