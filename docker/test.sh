#!/bin/bash

cd /usr/src/app/indexer
node --version
pnpm migration:run

# Eventually we will need to make it possible to run things in parallel. The
# biggest issue is that typeorm patterns use a lot of globals which makes
# substitution for parallel execution difficult.
NO_DYNAMIC_LOADS=true pnpm test -- --verbose=true --runInBand