ARG BASE_IMAGE=ghcr.io/opensource-observer/cloudquery-ts-base:latest

FROM ${BASE_IMAGE}

ARG PLUGIN_NAME

WORKDIR /usr/src/app/warehouse/cloudquery-${PLUGIN_NAME}

ENTRYPOINT [ "pnpm", "node", "--loader", "ts-node/esm", "src/main.ts" ]