---
title: Overview
sidebar_position: 1
---

The OSO architecture runs on the following platforms:

- Vercel: used to build and host the [frontend](https://www.opensource.observer), as well as the [documentation](https://docs.opensource.observer)
- [GitHub Actions](https://github.com/opensource-observer/oso/actions): used to continuously deploy everything else, including the data pipeline.
- [Google Cloud](./gcloud)
  - BigQuery - the data warehouse
  - CloudSQL - stores materialized views of the processed data for the API
- [Hasura](./hasura) - GraphQL API service
- [Supabase](./supabase) - user authentication and user database
