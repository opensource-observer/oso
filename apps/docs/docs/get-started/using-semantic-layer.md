---
title: "Using the Semantic Layer"
sidebar_position: 2
---

After some exploration with the OSO data, you may find that the available tables
have a complex set of relationships that can make it difficult to understand how
to properly write some set of queries. Understanding the relationships of the
tables key to being able to make meaningful queries against the OSO data. As
part of the the `pyoso`, we now include an experimental semantic layer.

The semantic layer provides a curated data model that can be used to query the
OSO data warehouse through a python interface. The explicit relationships and
attributes inherent in this semantic layer allow for automatically resolving
join paths, aggregations, and other aspects of using the data model so that
making informed queries doesn't require expertise in the universe of OSO tables.

## Querying against the semantic layer

### Overview

Before we get into a simple query, here's the overview of the most likely models
you'd be querying against:

- `artifacts` - This is a Semantic Model representing out `artifacts_v1` table.
  This includes everything from repositories, packages, blockchain addresses,
  and similar.
- `projects` - This is a Semantic Model representing our `projects_v1` table.
  This includes all of the projects gathered in both `oss-directory` and
  projects defined from [op-atlas](https://atlas.optimism.io/). Projects are
  comprised of artifacts. Often projects are simply the github organization for
  a set of repositories. However, they can also represent other groupings of
  artifacts.
- `collections` - This is a Semantic Model representing our `collections_v1`
  table. A collection is a grouping of projects. This grouping can be completely
  arbitrary.
- `int_events__github` - This is a Semantic Model representing our
  `int_events__github` table. Despite this being an intermediate table, it
  contains useful information that is likely useful for querying for github
  related events.
- `int_events__blockchain` - This is a Semantic Model representing our
  `int_events__blockchain` table. This table contains events related to
  blockchain transactions and other blockchain related events.
- `int_events__4337` - This is a Semantic Model representing our
  `int_events__4337` table. This table contains events related to ERC-4337
  transactions and other ERC-4337 related events.
- `metrics` - This is a Semantic Model representing our `metrics_v0` table. This
  table is not actually the metrics themselves, but rather a directory of the
  _available_ metrics.
- `timeseries_metrics_by_*` - These are a set of tables that actually represent
  the metrics for `artifacts`, `projects`, and `collections`. These tables are
  named based on the model they are associated with. For instance, the
  `timeseries_metrics_by_project_v1` table contains metrics for projects. These
  are the actual values where `metrics` is the directory of available metric
  types stored in these tables.

### A basic query

Let's consider a basic query that only seeks to find all artifacts within a
collection. If you only cared about the artifact name and collection name
attributes this semantic query would look like this:

```python
from pyoso import Client

oso = Client()

query = oso.semantic.select(
    "collection.name"
    "artifact.name",
)
```

This query simply `select`s the `name` attribute from both the `collection`
model and the `artifact` model.

To render this semantic query to sql you can do:

```python
print(query.sql())
```

By default this will use the trino SQL dialect and the printed query will look
something like this:

```sql
SELECT
  collection_db6d9b45.collection_name AS collection_name,
  artifact_8e5b948a.artifact_name AS artifact_name
FROM oso.artifacts_v1 AS artifact_8e5b948a
LEFT JOIN oso.artifacts_by_project_v1 AS artifacts_by_project_v1_4f760b72
  ON artifact_8e5b948a.artifact_id = artifacts_by_project_v1_4f760b72.artifact_id
LEFT JOIN oso.projects_v1 AS project_46f86faa
  ON artifacts_by_project_v1_4f760b72.project_id = project_46f86faa.project_id
LEFT JOIN oso.projects_by_collection_v1 AS projects_by_collection_v1_483e7c1c
  ON project_46f86faa.project_id = projects_by_collection_v1_483e7c1c.project_id
LEFT JOIN oso.collections_v1 AS collection_db6d9b45
  ON projects_by_collection_v1_483e7c1c.collection_id = collection_db6d9b45.collection_id
GROUP BY
  1,
  2
```

As evident in the generated sql, the semantic query tool automatically decides the proper join path and automatically groups the collection name and artifact name.

:::Note
For this specific example, a custom written query could produce one less
join, but due to the way the registry has is modeled this result is currently
as intended.
:::

To execute this generated sql query and return the associated dataframe one can simply do:

```python
df = query.as_pandas()
```

### Querying with a relationship

Relaltionships are a key part of the semantic layer. They allow us to define how models relate to each other. Unlike, SQL you don't explicity define join paths. The semantic layer resolves these paths for you. For dealing with relationships we have special semantics when a relationship attribute is included in the query.

#### Selecting just a relationship attribute

The `project` model has a relationship to the collection via it's `collection` relationship attribute.

```python
query = oso.semantic.select(
  "project.by_collection",
)
```

This would produce the following SQL:

```sql
SELECT
  projects_by_collection_v1_8247793e.collection_id AS project_collection
FROM oso.projects_v1 AS project_46f86faa
LEFT JOIN oso.projects_by_collection_v1 AS projects_by_collection_v1_8247793e
  ON project_46f86faa.project_id = projects_by_collection_v1_8247793e.project_id
GROUP BY
  1
```

When a relationship attribute is selected only the key used to reference the foreign model is returned. In the case of `project.collection`, the collection is referenced by it's collection id in a foreign key relationship.

We can also include the relationship attribute to provide a filtering
context without having an explicit filter. For instance if we wanted to only
get the project names that exist in _any_ collection, we could do this:

```python
query = oso.semantic.select(
    "project.name",
    "collection",
)
```

As not all artifacts are part of a project, this will only return the projects that have a relationship to a collection. This would produce the following SQL:

```sql
SELECT
  project_46f86faa.project_name AS project_name,
  project_46f86faa.collection_id AS project_collection
FROM oso.projects_v1 AS project_46f86faa
WHERE
  project_46f86faa.collection_id IS NOT NULL
GROUP BY
  1,
  2
```

#### Handling ambiguous joins

The previous examples only involved a fairly simple join relationships.
Artifacts are related to Collections via their relationship to Projects and some
intermediate tables in between. However, in the OSO data model we also have a
concept of Events. There are multiple event tables but let's consider the events
from github. In the current semantic layer the model responsible for the github
events is `github_event`. All of the event models have a generic interface that
involves the following relationships:

- `from` - The artifact that initiated an event
- `to` - The artifact that received an event

If we instead wanted to make the following semantic query:

```python
query = oso.semantic.select(
    "int_events__github.time",
    "collection.name",
    "artifact.name",
)
```

If you try to render this sql:

```python
query.sql()
```

This would result in a `ModelHasAmbiguousJoinPath` exception. This "ambiguous"
join is because there are two possible paths to join `github_event` to both the
`artifact` model the `collection` model. In such a case, we need to give the
semantic querying mechanism an explicit path for which to join against the
`github_event` table. To do this, we use a special arrow operator `->` that will
define the path we want to relate through for the ambiguous join. For instance,
if what we cared about are the event times and the associated artifacts and
collections that received an event we'd do this:

```python
query = oso.semantic.select(
    "int_events__github.time",
    "int_events__github.to->collection.name",
    "int_events__github.from->artifact.name",
)
```

This would then produce the following SQL:

```sql
SELECT
  collection_2083abff.collection_name AS int_events__github_to__collection_name,
  artifact_95a01095.artifact_name AS int_events__github_from__artifact_name,
  int_events__github_420c9a8e.time AS int_events__github_time
FROM oso.int_events__github AS int_events__github_420c9a8e
LEFT JOIN oso.artifacts_v1 AS artifact_1b71f23f
  ON int_events__github_420c9a8e.to_artifact_id = artifact_1b71f23f.artifact_id
LEFT JOIN oso.artifacts_by_project_v1 AS artifacts_by_project_v1_5ee26df1
  ON artifact_1b71f23f.artifact_id = artifacts_by_project_v1_5ee26df1.artifact_id
LEFT JOIN oso.projects_v1 AS project_e17705b6
  ON artifacts_by_project_v1_5ee26df1.project_id = project_e17705b6.project_id
LEFT JOIN oso.projects_by_collection_v1 AS projects_by_collection_v1_8247793e
  ON project_e17705b6.project_id = projects_by_collection_v1_8247793e.project_id
LEFT JOIN oso.collections_v1 AS collection_2083abff
  ON projects_by_collection_v1_8247793e.collection_id = collection_2083abff.collection_id
LEFT JOIN oso.artifacts_v1 AS artifact_95a01095
  ON github_event_420c9a8e.from_artifact_id = artifact_95a01095.artifact_id
GROUP BY
  1,
  2,
  3
```

## Filtering

Filtering is a key part of any query. The semantic layer provides a way to
filter on the attributes of the models. For instance, if we wanted to filter the
previous query to only include artifacts that are part of a specific namespace,
we could do this:

```python
query = oso.semantic.select(
    "int_events__github.time",
    "int_events__github.to->collection.name",
    "int_events__github.from->artifact.name",
).where(
    "int_events__github.to->artifact.namespace = 'oso'",
)
```

This would produce the following SQL:

```sql
SELECT
  collection_2083abff.collection_name AS int_events__github_to__collection_name,
  artifact_95a01095.artifact_name AS int_events__github_from__artifact_name,
  int_events__github_420c9a8e.time AS int_events__github_time
FROM oso.int_events__github AS int_events__github_420c9a8e
LEFT JOIN oso.artifacts_v1 AS artifact_1b71f23f
  ON int_events__github_420c9a8e.to_artifact_id = artifact_1b71f23f.artifact_id
LEFT JOIN oso.artifacts_by_project_v1 AS artifacts_by_project_v1_5ee26df1
  ON artifact_1b71f23f.artifact_id = artifacts_by_project_v1_5ee26df1.artifact_id
LEFT JOIN oso.projects_v1 AS project_e17705b6
  ON artifacts_by_project_v1_5ee26df1.project_id = project_e17705b6.project_id
LEFT JOIN oso.projects_by_collection_v1 AS projects_by_collection_v1_8247793e
  ON project_e17705b6.project_id = projects_by_collection_v1_8247793e.project_id
LEFT JOIN oso.collections_v1 AS collection_2083abff
  ON projects_by_collection_v1_8247793e.collection_id = collection_2083abff.collection_id
LEFT JOIN oso.artifacts_v1 AS artifact_95a01095
  ON github_event_420c9a8e.from_artifact_id = artifact_95a01095.artifact_id
WHERE
  artifact_1b71f23f.artifact_namespace = 'oso'
GROUP BY
  1,
  2,
  3
```

Additionally, you can also filter on a model's measures. Let's get all the artifacts with 1000 or less events:

```python
query = oso.semantic.select(
    "int_events__github.time",
    "int_events__github.to->collection.name",
    "int_events__github.to->artifact.name",
).where(
    "github_event.count <= 1000",
)
```

This would produce the following SQL:

```sql
SELECT
  collection_2083abff.collection_name AS int_events__github_to__collection_name,
  artifact_95a01095.artifact_name AS int_events__github_from__artifact_name,
  int_events__github_420c9a8e.time AS int_events__github_time
FROM oso.int_events__github AS int_events__github_420c9a8e
LEFT JOIN oso.artifacts_v1 AS artifact_1b71f23f
  ON int_events__github_420c9a8e.to_artifact_id = artifact_1b71f23f.artifact_id
LEFT JOIN oso.artifacts_by_project_v1 AS artifacts_by_project_v1_5ee26df1
  ON artifact_1b71f23f.artifact_id = artifacts_by_project_v1_5ee26df1.artifact_id
LEFT JOIN oso.projects_v1 AS project_e17705b6
  ON artifacts_by_project_v1_5ee26df1.project_id = project_e17705b6.project_id
LEFT JOIN oso.projects_by_collection_v1 AS projects_by_collection_v1_8247793e
  ON project_e17705b6.project_id = projects_by_collection_v1_8247793e.project_id
LEFT JOIN oso.collections_v1 AS collection_2083abff
  ON projects_by_collection_v1_8247793e.collection_id = collection_2083abff.collection_id
LEFT JOIN oso.artifacts_v1 AS artifact_95a01095
  ON github_event_420c9a8e.from_artifact_id = artifact_95a01095.artifact_id
GROUP BY
  1,
  2,
  3
HAVING
  COUNT(github_event_420c9a8e.event_id) <= 1000
```

## Chaining and reusing queries

The semantic layer also provides a way to chain multiple queries together. In
the same way that one may define CTEs in SQL, a named query allows us to
reference a query as if it were just another model in the semantic layer. This
can only happen within a single query builder context, so you must use the same
`oso.semantic` instance to chain queries together that you wish to reuse. In
order to support this, you must name a query using the `with_select` method. The
first argument to this method is the name of the query. Then in subsequent
queries you can reference that query as if it were just another model in the
semantic layer.

Let's find all the projects that published at least one new release in the last
6 months and also had a user operation in ERC-4337.

:::Note
This is not yet implemented and this design may need to change.
:::

```python
github_release_metrics = oso.semantic.select(
    "timeseries_metrics_by_project.sum as metric_sum",
    "timeseries_metrics_by_project.project as project"
).where(
    "metrics.name LIKE 'GITHUB_releases_monthly'"
)

# Get the received grants by selecting `projects.*`
received_grants = oso.semantic.cte(
  "github_release_metrics", github_release_metrics
).select(
    "projects"
).where(
    "github_release_metrics.metric.sum > 0"
)

paymaster_projects = oso.semantic.select(
    "int_events__4337.to",
).where(
    "int_events__4337.event_type LIKE 'CONTRACT_INVOCATION_VIA_PAYMASTER'"
)

filtered_projects = oso.semantic.cte(
    "paymaster_projects",
    paymaster_projects
).cte(
   "received_grants",
    received_grants
).select(
    "paymaster_projects.to",
    "received_grants.projects",
)

final = oso.semantic.cte(
  "filtered_projects",
  filtered_projects
).select(
    "filtered_projects.name",
).where(
    "filtered_projects.project_name IS NOT NULL",
)
```

This query will produce the following SQL similar to the following:

```sql
-- This query is not exactly correct we need to render this once this part of the code is implemented
with github_release_metrics as (
  SELECT
    SUM(timeseries_metrics_by_project_v1_4f760b72.amount) AS metric_sum,
    timeseries_metrics_by_project_v1_4f760b72.project_id AS project
  FROM oso.timeseries_metrics_by_project_v1 AS timeseries_metrics_by_project_v1_4f760b72
  LEFT JOIN oso.metrics_v0 AS metrics_v0_5ee26df1
    ON timeseries_metrics_by_project_v1_4f760b72.metric_id = metrics_v0_5ee26df1.metric_id
  WHERE
    metrics_v0_5ee26df1.name LIKE 'GITHUB_releases_monthly'
  GROUP BY
    2
),
received_grants as (
  SELECT
    project_46f86faa.project_id AS project_id
  FROM github_release_metrics as github_release_metrics_13371337
  LEFT JOIN oso.projects_v1 AS project_46f86faa
    ON github_release_metrics_13371337.project = project_46f86faa.project_id
  WHERE
    github_release_metrics_13371337.metric_sum > 0
  GROUP BY
    1
),
paymaster_projects as (
  SELECT
    4337_events_420c9a8e.to_artifact_id AS to_artifact_id
  FROM oso.int_events__4337 AS 4337_events_420c9a8e
  WHERE
    4337_events_420c9a8e.event_type LIKE 'CONTRACT_INVOCATION_VIA_PAYMASTER'
  GROUP BY
    1
),
filtered_projects as (
  SELECT
    project_46f86faa.*,
    paymaster_projects_8247793e.to_artifact_id AS to_artifact_id,
    received_grants_5ee26df1.project_id AS project_id
  FROM oso.projects_v1 AS project_46f86faa
  LEFT JOIN paymaster_projects AS paymaster_projects_8247793e
    ON project_46f86faa.project_id = paymaster_projects_8247793e.to_artifact_id
  LEFT JOIN received_grants AS received_grants_5ee26df1
    ON project_46f86faa.project_id = received_grants_5ee26df1.project_id
  WHERE
    project_46f86faa.project_name IS NOT NULL
  GROUP BY
    1, 2, 3, 4, 5, 6, 7, 8
)
SELECT
  filtered_projects_5ee26df1.project_name AS filtered_projects_name
FROM filtered_projects AS filtered_projects_5ee26df1
GROUP BY
  1
```

### Star querying

The semantic layer doesn't support star querying in the same way that SQL does. In order to get all of the fields from a model you instead simply reference the model itself. For instance, if you wanted to get all of the fields from the `artifact` model, you would do this:

```python
query = oso.semantic.select(
    "artifact"
)
```

This is more useful when combined with a filter. For instance, if you wanted to get all of the fields from the `artifact` model where the artifact is part of a specific collection, you would do this:

```python
query = oso.semantic.select(
    "artifact",
).where(
    "collection.name = 'my_collection'",
)
```

### Querying a relationship attribute

While not _always_ useful, it is possible to simply query a relationship
attribute. While not always useful on it's own, this can be important to use
when reusing queries as the semantic layer will automatically.

```python
query = registry.select(
    "project",
    ["by_collection"],
)
print(query.sql(pretty=True))
```

The output of this query will look like this:

```sql
SELECT
    artifact.artifact_id as artifact__by_project
FROM iceberg.oso.artifacts_v1 as artifact
```

The importance of this query is that assuming that not all projects have
artifacts, this query will return all projects that actually have artifacts.

When using reusing a query this ensures that the `Relationship` is maintained
and can be used by downstream queries.

Like this:

```python
source_more_than_100_artifacts = registry.select(
  "artifact.source as source",
  "artifact.by_project as by_project"
).where(
    "artifact.count > 100"
)

registry.cte(
    "source_more_than_100_artifacts",
    source_more_than_100_artifacts
).select(
    "source_more_than_100_artifacts.source",
    "project.name",
)
```

This contrived example will produce a result that returns all projects related
to artifact source that have more than 100 artifacts.
