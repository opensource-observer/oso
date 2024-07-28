# Hasura configuration

This directory stores all configurations for the Hasura deployment.
Hasura is currently setup with only a single subgraph, `oso_subgraph`,
with a single connector `oso_clickhouse`.

_Note: This only works for Hasura version 3 (aka DDN)._

## Setup

Copy `.env.example` to `.env` and set the environment variables as needed.
You can get your Hasura PAT by running

```bash
ddn auth print-pat
```

In `./oso_subgraph/`, copy `.env.oso_subgraph.example` to `.env.oso_subgraph.cloud` and `.env.oso_subgraph.local`. These need to be configured to your Clickhouse connector deployment. The local deployment will be launched by Docker compose, where was the cloud deployment is hosted by Hasura.

In `./oso_subgraph/connector/oso_clickhouse`, copy `.env.example` to `.env.cloud` and `.env.local`. Populate with Clickhouse credentials.

## Sync schema with Clickhouse

## Configure

You can modify any files to update the Hasura configuration.
See the
[Hasura docs](https://hasura.io/docs/3.0/) to learn more.

Note that anything in `./oso_subgraph/metadata/` will be overwritten by the build step.

## Build

This will idempotently update table configurations for all tables found in the Clickhouse database.
This needs to be run every time the schema changes.
For more information, see `./src/cli.ts`.

```bash
pnpm build
```

## Deploy

To reload the database schemas and apply the metadata configurations, run:

```bash
pnpm run deploy
```

For more information on how to manage metadata, see the
[Hasura guide](https://hasura.io/docs/latest/migrations-metadata-seeds/manage-metadata/#reload-metadata).
