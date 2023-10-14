# OSO frontend app

This frontend is configured for the Next.js app router, which makes heavy use of SSR and RSC to generate pages on demand for data found in the database.

All data is access through a Hasura GraphQL engine. In the future, we may be able to run this on Cloudflare workers/pages in the edge runtime due to this architecture decision.

## Configure

Make sure you have a `.env.local` properly populated with all configuration variables.
These will be required to build.

## Dependent services

The application will query a GraphQL service both server-side and client-side.
We assume you have a Hasura instance running at a URL configured by
`NEXT_PUBLIC_DB_GRAPHQL_URL`.

We run a Hasura cloud instance, but you can also setup a local Hasura instance.

1. Navigate to `../indexer`.
2. Populate `.env` with the proper database configuration
3. Make sure you have `docker` installed on your machine.
4. Run `../indexer/utilities/database/hasura.sh` to pull the latest Hasura docker image and run it.

If you are using our production database, we'll already have configurations in the `hdb_catalog` schema. If you are spinning up a new Postgres database, then you'll have to:

1. Run the TypeORM migrations to create the entities
2. Navigate to the `Data` tab, and track the following tables and all related relations:

- artifact
- collection
- collection_projects_project
- events_daily_by_artifact
- events_daily_by_project
- project
- project_artifacts_artifact

## Install dependencies

We typically use `pnpm` for package management.

```bash
pnpm install
```

## Build, lint, test

To build, lint, and test, run the following

```bash
pnpm build
pnpm lint
pnpm test
```

You can also serve built files with

```bash
pnpm start
```

### GraphQL queries

We codegen types for all GraphQL queries. If you make changes, make sure to run

```bash
pnpm graphql:compile
```

## Run the dev server

To run the dev server, which will also automatically watch for changes from Plasmic:

```bash
pnpm dev
```

Remember to set `preview: true` in `plasmic-init.ts` if you want to see unpublished changes from Plasmic Studio.

## Deploy

Currently, all deployments are automatically handled by Vercel's GitHub app.
