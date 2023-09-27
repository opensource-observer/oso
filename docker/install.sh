set -euxo pipefail

npm install -g pnpm
pnpm install
# For now let's just build the indexer
pnpm build