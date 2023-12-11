set -euxo pipefail

npm install -g pnpm
pnpm i --frozen-lockfile
# For now let's just build the indexer
pnpm build:indexer