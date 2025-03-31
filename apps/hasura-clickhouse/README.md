# Hasura configuration

This directory stores all configurations for the Hasura deployment.
Hasura is currently setup with only a single subgraph, `oso_subgraph`,
with a single connector `oso_clickhouse`.

_Note: This only works for Hasura version 3 (aka DDN)._

## Setup

### Install `ddn`

First install the `ddn` CLI tool from Hasura

```bash
curl -L https://graphql-engine-cdn.hasura.io/ddn/cli/v3/get.sh | bash
```

### Configure environment

Copy `.env.example` to `.env` and set the environment variables as needed.
You can get your Hasura PAT by running

```bash
ddn auth print-pat
```

In `./oso_subgraph/`, copy `.env.oso_subgraph.example` to `.env.oso_subgraph.cloud` and `.env.oso_subgraph.local`. These need to be configured to your Clickhouse connector deployment. The local deployment will be launched by Docker compose, where was the cloud deployment is hosted by Hasura.

In `./oso_subgraph/connector/oso_clickhouse`, copy `.env.example` to `.env.cloud` and `.env.local`. Populate with Clickhouse credentials.

### Build

```bash
pnpm install
pnpm build
```

## Sync schema with Clickhouse

Pull the latest Clickhouse schema

```bash
pnpm sync
```

Note, under the hood, this will do the following steps:

- Introspect the database and store the entire schema in a configuration file (`pnpm metadata:introspect`)
- Add all of the versioned models to the Hasura API (`pnpm metadata:add`)
- Automatically update the Hasura metadata files to fit the OSO policy (`pnpm metadata:update`)

You either can script changes to the Hasura metadata through `./src/cli.ts`
or manually modify any files to update the Hasura configuration.
See the [Hasura docs](https://hasura.io/docs/3.0/) to learn more.

## Deploy

To apply the metadata configurations to Hasura cloud, run:

```bash
pnpm run deploy
```

## Run locally

Start a local Hasura instance.
If you don't run it locally, the sync command will load an ephemeral container

```bash
pnpm start
```

## FAQ

If you build and deploy a version without applying it as the default one, you'll need to do that explicitly

```bash
ddn supergraph build apply BUILD_ID
# ddn supergraph build apply 030c5f3ce0
```
