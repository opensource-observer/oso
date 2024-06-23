---
title: Use the GraphQL API
sidebar_position: 2
---

The OSO API currently only allows read-only GraphQL queries against OSO mart models
(e.g. impact metrics, project info).
This API should only be used to fetch data to integrate into a live application in production.
For data exploration, check out the guides on
[performing queries](./query-data.mdx)
and [Python notebooks](./python-notebooks.md).

## Generate an API key

First, navigate to [www.opensource.observer](https://www.opensource.observer) and create a new account.

If you already have an account, log in. Then create a new personal API key:

1. Go to [Account settings](https://www.opensource.observer/app/settings)
2. In the "API Keys" section, click "+ New"
3. Give your key a label - this is just for you, usually to describe a key's purpose.
4. You should see your brand new key. **Immediately** save this value, as you'll **never** see it again after refreshing the page.
5. Click "Create" to save the key.

You can create as many keys as you like.

![generate API key](./generate-api-key.png)

## GraphQL Endpoint

All API requests are sent to the following URL:

```
https://opensource-observer.hasura.app/v1/graphql
```

You can navigate to our
[public GraphQL explorer](https://cloud.hasura.io/public/graphiql?endpoint=https://opensource-observer.hasura.app/v1/graphql)
to explore the schema and execute test queries.

## Authentication

In order to authenticate with the API service, you have to use the `Authorization` HTTP header and `Bearer` authentication on all HTTP requests, like so:

```js
const headers = {
  Authorization: `Bearer ${DEVELOPER_API_KEY}`,
};
```

:::tip
Our API opens a small rate limit for anonymous queries without authentication. Feel free to use for low volume queries.
:::

## Example

This query will fetch the first 10 projects in
[oss-directory](https://github.com/opensource-observer/oss-directory).

```graphql
query GetProjects {
  projects_v1(limit: 10) {
    project_id
    project_name
    display_name
    description
  }
}
```

This query will fetch **code metrics** for 10 projects, ordered by `star_count`.

```graphql
query GetCodeMetrics {
  code_metrics_by_project_v1(
    limit: 10
    order_by: { star_count: desc_nulls_last }
  ) {
    project_id
    project_name
    event_source
    star_count
    fork_count
    contributor_count
  }
}
```

## GraphQL Explorer

The GraphQL schema is automatically generated from [`oso/dbt/models/marts`](https://github.com/opensource-observer/oso/tree/main/dbt/models/marts). Any dbt model defined there will automatically be exported to our GraphQL API. See the guide on [adding DBT models](../contribute/impact-models.md) for more information on contributing to our marts models.

:::warning
Our data pipeline is under heavy development and all table schemas are subject to change until we introduce versioning to marts models.
Please join us on [Discord](https://www.opensource.observer/discord) to stay up to date on updates.
:::

You can navigate to our [public GraphQL explorer](https://cloud.hasura.io/public/graphiql?endpoint=https://opensource-observer.hasura.app/v1/graphql) to explore the schema and execute test queries.

![GraphQL explorer](./graphql-explorer.png)

## Rate Limits

All requests are rate limited. There are currently 2 separate rate limits for different resources:

- **anonymous**: Anyone can make a query, even without an authorization token, subject to a low rate limit.
- **developer**: Developers who have been accepted into the [Kariba Data Collective](https://www.kariba.network) and provide an API key in the HTTP header will be subject to a higher rate limit.

:::warning
We are still currently adjusting our rate limits based on capacity and demand. If you feel like your rate limit is too low, please reach out to us on our [Discord](https://www.opensource.observer/discord).
:::
