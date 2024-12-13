---
title: Deep Dive into a Project
sidebar_position: 2
---

Analyze detailed metrics for a specific project. New to OSO? Check out our [Getting Started guide](../get-started/index.md) to set up your BigQuery or API access.

:::tip
All **projects** are defined as YAML files in [OSS Directory](https://github.com/opensource-observer/oss-directory). View our current projects [here](https://github.com/opensource-observer/oss-directory/tree/main/data/projects).
:::

## BigQuery

If you haven't already, then the first step is to subscribe to OSO public datasets in BigQuery. You can do this by clicking the "Subscribe" button on our [Datasets page](../integrate/overview/#oso-production-data-pipeline).

The following queries should work if you copy-paste them into your [BigQuery console](https://console.cloud.google.com/bigquery).

### Find a project

Search for projects by name:

```sql
select
  project_id,
  project_name,
  display_name
from `oso_production.projects_v1`
where lower(display_name) like lower('%merkle%')
```

### Find a project by artifact

Find projects associated with specific artifacts (e.g., GitHub repositories, contracts):

```sql
select
  project_id,
  project_name,
  artifact_namespace as github_owner,
  artifact_name as github_repo
from `oso_production.artifacts_by_project_v1`
where
  artifact_source = 'GITHUB'
  and artifact_namespace like '%uniswap%'
```

### Code metrics

Get code metrics for a specific project:

```sql
select
  project_name,
  display_name,
  star_count,
  fork_count,
  commit_count_6_months,
  contributor_count_6_months
from `oso_production.code_metrics_by_project_v1`
where project_name = 'opensource-observer'
```

### Timeseries metrics

Get historical metrics for a project:

```sql
select
  tm.sample_date,
  m.metric_name,
  tm.amount
from `oso_production.timeseries_metrics_by_project_v0` as tm
join `oso_production.metrics_v0` as m
  on tm.metric_id = m.metric_id
join `oso_production.projects_v1` as p
  on tm.project_id = p.project_id
where p.project_name = 'wevm'
order by sample_date desc
```

### Code contributors

Get all contributors to a project's GitHub repositories:

```sql
select
  te.time,
  a.artifact_name as code_contributor,
  abp.artifact_name as github_repo,
  te.event_type,
  te.amount
from `oso_production.timeseries_events_by_artifact_v0` as te
join `oso_production.artifacts_by_project_v1` as abp
  on te.to_artifact_id = abp.artifact_id
join `oso_production.artifacts_v1` a
  on te.from_artifact_id = a.artifact_id
where
  abp.project_name = 'ipfs'
  and te.event_type = 'COMMIT_CODE'
order by te.time desc
```

## GraphQL

The following queries should work if you copy-paste them into our [GraphQL sandbox](https://www.opensource.observer/graphql). For more information on how to use the GraphQL API, check out our [GraphQL guide](../integrate/api.md).

### Find a project

Search for projects by name:

```graphql
query FindProject {
  oso_projectsV1(where: { display_name: { _ilike: "%ethereum%" } }) {
    projectId
    projectName
    displayName
  }
}
```

### Find a project by artifact

Find projects associated with specific artifacts:

```graphql
query FindProjectByArtifact {
  oso_artifactsByProjectV1(
    where: {
      artifactNamespace: { _ilike: "%uniswap%" }
      artifactSource: { _eq: "GITHUB" }
    }
  ) {
    projectId
    projectName
    artifactNamespace
    artifactName
  }
}
```

### Code metrics

Get code metrics for a specific project:

```graphql
query CodeMetricsForProject {
  oso_codeMetricsByProjectV1(
    where: { projectName: { _eq: "opensource-observer" } }
  ) {
    projectName
    displayName
    starCount
    forkCount
    commitCount6Months
    contributorCount6Months
  }
}
```

### Timeseries metrics

Get historical metrics for a project. This query returns two tables, `timeseriesMetrics` and `metrics`, which can be joined client-side on `metricId`.

```graphql
query TimeseriesMetrics {
  timeseriesMetrics: oso_timeseriesMetricsByProjectV0(
    where: {
      projectId: { _eq: "Erx9J64anc8oSeN-wDKm0sojJf8ONrFVYbQ7GFnqSyc=" }
    }
  ) {
    sampleDate
    metricId
    amount
  }
  metrics: oso_metricsV0 {
    metricId
    metricName
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

### Find a project

Search for projects by name:

```python
query = """
  select
    project_id,
    project_name,
    display_name
  from `oso_production.projects_v1`
  where lower(display_name) like lower('%merkle%')
"""
df = client.query(query).to_dataframe()
```

### Find a project by artifact

Find projects associated with specific artifacts:

```python
query = """
  select
    project_id,
    project_name,
    artifact_namespace as github_owner,
    artifact_name as github_repo
  from `oso_production.artifacts_by_project_v1`
  where
    artifact_source = 'GITHUB'
    and artifact_namespace like '%uniswap%'
"""
df = client.query(query).to_dataframe()
```

### Code metrics

Get code metrics for a specific project:

```python
query = """
  select
    project_name,
    display_name,
    star_count,
    fork_count,
    commit_count_6_months,
    contributor_count_6_months
  from `oso_production.code_metrics_by_project_v1`
  where project_name = 'opensource-observer'
"""
df = client.query(query).to_dataframe()
```

### Timeseries metrics

Get historical metrics for a project:

```python
query = """
  select
    tm.sample_date,
    m.metric_name,
    tm.amount
  from `oso_production.timeseries_metrics_by_project_v0` as tm
  join `oso_production.metrics_v0` as m
    on tm.metric_id = m.metric_id
  join `oso_production.projects_v1` as p
    on tm.project_id = p.project_id
  where p.project_name = 'wevm'
  order by sample_date desc
"""
df = client.query(query).to_dataframe()
```

### Code contributors

Get all contributors to a project's GitHub repositories:

```python
query = """
  select
    te.time,
    a.artifact_name as code_contributor,
    abp.artifact_name as github_repo,
    te.event_type,
    te.amount
  from `oso_production.timeseries_events_by_artifact_v0` as te
  join `oso_production.artifacts_by_project_v1` as abp
    on te.to_artifact_id = abp.artifact_id
  join `oso_production.artifacts_v1` a
    on te.from_artifact_id = a.artifact_id
  where
    abp.project_name = 'ipfs'
    and te.event_type = 'COMMIT_CODE'
  order by te.time desc
"""
df = client.query(query).to_dataframe()
```

## Adding projects

Projects are defined as YAML files in our [OSS Directory repo](https://github.com/opensource-observer/oss-directory). You can add or update your own projects or project artifacts by submitting a pull request.

For more information on how projects work, see our guide [here](../guides/oss-directory/project.md).
