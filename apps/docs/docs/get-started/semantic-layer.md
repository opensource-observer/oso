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

## Anatomy of the semantic layer

The semantic layer provides an interface that takes a lot of inspiration from
the wonderful work at cube.dev. Many of the same abstractions are used to provide a similar vocabulary for those familiar with that tool. These abstractions and components are as such:

- `Model`
  - A model is a given object abstraction in for a given data type in the OSO
    data warehouse. At this time, it is expected that there's a single
    canonical table to represent a given Model. Models, like any object can
    relate to each other. For instance, the OSO data model has the concept of
    an Artifact which is part of zero or more Projects, and Projects which are
    part of zero or more Collections. Each of those entities are related to
    their associated Models.
- `Dimension`
  - A dimension is a non-aggregated attribute of a model. This could be
    something like an Artifact name, a Project namespace, a Collection
    description, an Event type, or Event time.
- `Measure`
  - A measure is an aggregated attribute of a model that is usually used to summarize values related to a model. This could be something like, the count of Artfiacts or sum of the amount dimension of Events.
- `Relationship`
  - A relationship defines a relationship is a special attribute that defines
    the relationship between one model and another. In sql, this is modelled as
    some kind of foreign key.
- `Interface`
  - Much like an interface in an object oriented language, an interface is a generic interface that can be applied to a given model. This allows us to provide
- `Registry`
  - A registry is the directory of all the models and their relationships to
    each other. Without the registry it's impossible to create a valid sql
    query.

_Note:_ This guide is all about using the semantic layer and not defining it. If
you'd like to contribute to the semantic layer by defining additional models,
relationships, etc, see the guide
[here](../contribute-models/semantic-layer-definition.md)

## Querying against the semantic layer

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

_Note:_ For this specific example, a custom written query could produce one less
join, but due to the way the registry has is modeled this result is currently
as intended.

To execute this generated sql query and return the associated dataframe one can simply do:

```python
df = query.as_pandas()
```

### Handling ambiguous joins

The previous example only involved a fairly simple join relationship. Artifacts
are related to Collections via their relationship to Projects and some intermediate tables in between. However, in the OSO data model we also have a concept of Events. There are multiple event tables but let's consider the events from github. In the current semantic layer the model responsible for the github events is `github_event`. All of the event models have a generic interface that involves the following relationships:

- `from` - The artifact that initiated an event
- `to` - The artifact that received an event

If we instead wanted to make the following semantic query:

```python
query = oso.semantic.select(
    "github_event.time",
    "collection.name"
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
    "github_event.time",
    "github_event.to->collection.name"
    "github_event.to->artifact.name",
)
```

This would then produce the following SQL:

```sql
SELECT
  collection_2083abff.collection_name AS github_event_to__collection_name,
  artifact_95a01095.artifact_name AS github_event_from__artifact_name,
  github_event_420c9a8e.time AS github_event_time
FROM oso.int_events__github AS github_event_420c9a8e
LEFT JOIN oso.artifacts_v1 AS artifact_1b71f23f
  ON github_event_420c9a8e.to_artifact_id = artifact_1b71f23f.artifact_id
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

## Chaining

## Full Reference

Much like the OSO data model itself, the object model of the semantic layer is a
dynamic and frequently changing set of abstractions. As such, the reference
documentation of the semantic model is versioned and available [here](?). As the semantic model updates, so too does this living document.
