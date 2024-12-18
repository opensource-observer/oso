---
title: Analyze a Collection of Projects
sidebar_position: 1
---

Get a high level view of key metrics for a collection of projects. New to OSO? Check out our [Getting Started guide](../get-started/index.md) to set up your BigQuery or API access.

:::tip
All **collections** are defined as YAML files in [OSS Directory](https://github.com/opensource-observer/oss-directory). View our current collections [here](https://github.com/opensource-observer/oss-directory/tree/main/data/collections).
:::

## BigQuery

If you haven't already, then the first step is to subscribe to OSO public datasets in BigQuery. You can do this by clicking the "Subscribe" button on our [Datasets page](../integrate/datasets/#oso-production-data-pipeline).

The following queries should work if you copy-paste them into your [BigQuery console](https://console.cloud.google.com/bigquery).

### All collections

Get the names of all collections on OSO:

```sql
select
  collection_name,
  display_name
from `oso_production.collections_v1`
order by collection_name
```

### Projects in a collection

Get the names of all projects in a collection:

```sql
select
  project_id,
  project_name
from `oso_production.projects_by_collection_v1`
where collection_name = 'gg-01'
```

### Code metrics

Get code metrics for all projects in a collection:

```sql
select cm.*
from `oso_production.code_metrics_by_project_v1` as cm
join `oso_production.projects_by_collection_v1` as pbc
  on cm.project_id = pbc.project_id
where pbc.collection_name = 'ethereum-crypto-ecosystems'
```

### Onchain metrics

Get onchain metrics for all projects in a collection:

```sql
select om.*
from `oso_production.onchain_metrics_by_project_v1` as om
join `oso_production.projects_by_collection_v1` as pbc
  on om.project_id = pbc.project_id
where pbc.collection_name = 'optimism'
```

### Funding metrics

Get funding metrics for all projects in a collection:

```sql
select fm.*
from `oso_production.funding_metrics_by_project_v1` as fm
join `oso_production.projects_by_collection_v1` as pbc
  on fm.project_id = pbc.project_id
where pbc.collection_name = 'op-rpgf3'
```

## GraphQL

The following queries should work if you copy-paste them into our [GraphQL sandbox](https://www.opensource.observer/graphql). For more information on how to use the GraphQL API, check out our [GraphQL guide](../integrate/api.md).

### All collections

Get the names of all collections on OSO:

```graphql
query Collections {
  oso_collectionsV1 {
    collectionName
    displayName
  }
}
```

### Projects in a collection

Get the names of all projects in a collection:

```graphql
query ProjectsInCollection {
  oso_projectsByCollectionV1(where: { collectionName: { _eq: "gg-01" } }) {
    projectId
    projectName
  }
}
```

### Code metrics

Get code metrics for all projects in a collection. This query returns two tables, `metrics` and `projects`, which can be joined client-side on `projectId`.

```graphql
query CodeMetricsQuery {
  metrics: oso_codeMetricsByProjectV1 {
    projectId
    starCount
    forkCount
    commitCount6Months
    contributorCount6Months
  }
  projects: oso_projectsByCollectionV1(
    where: { collectionName: { _eq: "ethereum-crypto-ecosystems" } }
  ) {
    projectId
  }
}
```

### Onchain metrics

Get onchain metrics for all projects in a collection. This query returns two tables, `metrics` and `projects`, which can be joined client-side on `projectId`.

```graphql
query OnchainMetricsQuery {
  metrics: oso_onchainMetricsByProjectV1 {
    projectId
    transactionCount6Months
    gasFeesSum6Months
    newAddressCount90Days
  }
  projects: oso_projectsByCollectionV1(
    where: { collectionName: { _eq: "optimism" } }
  ) {
    projectId
  }
}
```

### Funding metrics

Get funding metrics for all projects in a collection. This query returns two tables, `metrics` and `projects`, which can be joined client-side on `projectId`.

```graphql
query FundingMetricsQuery {
  metrics: oso_fundingMetricsByProjectV1 {
    projectId
    totalFundingReceivedUsd6Months
  }
  projects: oso_projectsByCollectionV1(
    where: { collectionName: { _eq: "op-rpgf3" } }
  ) {
    projectId
  }
}
```

## Python

See our guide on [writing Python notebooks](../integrate/python-notebooks.md) for more information on how to connect to BigQuery and query data. Our [Insights Repo](https://github.com/opensource-observer/insights) is full of examples too.

### Connect to BigQuery

You can use the following to connect to BigQuery:

```python
from google.cloud import bigquery
import pandas as pd
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = # PATH TO YOUR CREDENTIALS JSON
GCP_PROJECT = # YOUR GCP PROJECT NAME

client = bigquery.Client(GCP_PROJECT)
```

### All collections

Get the names of all collections on OSO:

```python
query = """
  select
    collection_name,
    display_name
  from `oso_production.collections_v1`
  order by collection_name
"""
df = client.query(query).to_dataframe()
```

### Projects in a collection

Get the names of all projects in a collection:

```python
query = """
  select
    project_id,
    project_name
  from `oso_production.projects_by_collection_v1`
  where collection_name = 'gg-01'
"""
df = client.query(query).to_dataframe()
```

### Code metrics

Get code metrics for all projects in a collection:

```python
query = """
  select cm.*
  from `oso_production.code_metrics_by_project_v1` as cm
  join `oso_production.projects_by_collection_v1` as pbc
    on cm.project_id = pbc.project_id
  where pbc.collection_name = 'ethereum-crypto-ecosystems'
"""
df = client.query(query).to_dataframe()
```

### Onchain metrics

Get onchain metrics for all projects in a collection:

```python
query = """
  select om.*
  from `oso_production.onchain_metrics_by_project_v1` as om
  join `oso_production.projects_by_collection_v1` as pbc
    on om.project_id = pbc.project_id
  where pbc.collection_name = 'optimism'
"""
df = client.query(query).to_dataframe()
```

### Funding metrics

Get funding metrics for all projects in a collection:

```python
query = """
  select fm.*
  from `oso_production.funding_metrics_by_project_v1` as fm
  join `oso_production.projects_by_collection_v1` as pbc
    on fm.project_id = pbc.project_id
  where pbc.collection_name = 'op-rpgf3'
"""
df = client.query(query).to_dataframe()
```

## Adding collections and projects

Projects and collections are defined as YAML files in our [OSS Directory repo](https://github.com/opensource-observer/oss-directory). You can add or update your own collections and projects by submitting a pull request.

For more information on how collections work, see our guide [here](../guides/oss-directory/collection.md).
