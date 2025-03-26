---
title: Hasura
sidebar_position: 3
---

We currently use Hasura v3 (DDN) for serving the GraphQL API.
Hasura will auto-generate the GraphQL schema by introspecting
the consumer Trino cluster.

## Metadata

Any configurations outside of environment variables should be set via metadata in the OSO repository.
For more info on how to do this, check out the
[README](https://github.com/opensource-observer/oso/tree/main/apps/hasura-trino) under `./apps/hasura-trino`.
