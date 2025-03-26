---
title: Overview
sidebar_position: 0
---

[OSO Service Definition](./service)

The OSO architecture runs on the following platforms:

- Vercel: used to build and host the [frontend](https://www.opensource.observer)
- Cloudflare Pages: used to host the [documentation](https://docs.opensource.observer)
- [GitHub Actions](https://github.com/opensource-observer/oso/actions): used for CI/CD
- [Google Cloud](./gcloud): self-managed k8s for Trino, Iceberg and Dagster
- [Hasura](./hasura): GraphQL API service
- [Supabase](./supabase): user authentication and user database
