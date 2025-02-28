---
title: Hasura
sidebar_position: 3
---

## Setup

When setting up Hasura, the main things that need to be configured are the environment variables.
For a complete list of environment variables, see the
[Hasura reference](https://hasura.io/docs/latest/deployment/graphql-engine-flags/reference/).

- Env vars:
  - `HASURA_GRAPHQL_ADMIN_SECRET`: choose a random password
  - `HASURA_GRAPHQL_CORS_DOMAIN`: "\*"
  - `HASURA_GRAPHQL_UNAUTHORIZED_ROLE`: "anonymous"
  - `HASURA_GRAPHQL_DATABASE_URL`: enter the connection string for the Postgres database
  - `HASURA_GRAPHQL_AUTH_HOOK`: "https://www.opensource.observer/api/auth"
- Domains: follow the prompt to enable a custom domain at `api.opensource.observer`.

## Metadata

Any configurations outside of environment variables should be set via metadata in the OSO repository.
For more info on how to do this, check out the
[README](https://github.com/opensource-observer/oso/tree/main/hasura) under `./apps/hasura`.
