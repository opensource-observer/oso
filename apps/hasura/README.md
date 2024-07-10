# Hasura configuration

This directory stores all configurations for the Hasura deployment.

## Setup

Copy `.env.example` to `.env` and set the environment variables as needed.

## Configure

You can modify any files in `./metadata` to update the Hasura configuration.
See the
[Hasura metadata reference](https://hasura.io/docs/latest/migrations-metadata-seeds/metadata-format/) on the schema.

Note that anything in `./metadata/databases/cloudsql/tables/`
will be overwritten by the build step.

## Build

This will generate table configurations for all tables found in `/warehouse/dbt/models/`.
This needs to be run every time the schema changes.
For more information, see `./src/genTables.ts`.

```bash
pnpm build
pnpm gen:tables
```

## Deploy

To reload the database schemas and apply the metadata configurations, run:

```bash
pnpm run deploy
```

For more information on how to manage metadata, see the
[Hasura guide](https://hasura.io/docs/latest/migrations-metadata-seeds/manage-metadata/#reload-metadata).
