set -euxo pipefail

# Ensure all of the node modules directorys aren't empty. A change in pnpm v8.12
# caused it to attempt deletion of empty node_modules directories. This fixes
# that issue.
touch /usr/src/app/node_modules/.noop
touch /usr/src/app/indexer/node_modules/.noop
touch /usr/src/app/frontend/node_modules/.noop
touch /usr/src/app/docs/node_modules/.noop

npm install -g pnpm
node -v

pnpm i --frozen-lockfile --ignore-scripts

# For now let's just build the indexer
pnpm build:indexer 