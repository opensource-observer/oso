---
title: Core Data Modeling Concepts
sidebar_position: 2
---

:::info
This guide explains the fundamental concepts behind OSO's data models, including entities, events, metrics, and the overall model structure.
:::

## Core Concepts

OSO unifies data from different sources into consistent data models that can be queried and analyzed at scale. In order to contribute models, it's important to understand the core concepts and structures used in OSO.

### Entities

Entities represent people, organizations, repositories, packages, and much more. Every entity has a unique ID comprised of a source, namespace, and name. These IDs are used to link entities across different data sources and models.

Some examples:

- A GitHub repo, e.g. "https://github.com/opensource-observer/oso", is assigned `@oso_entity_id('GITHUB', 'opensource-observer', 'oso')`
- An address on Base, e.g., "0x1234...", is assigned `@oso_entity_id('BASE', '', '0x1234...')`
- A project in (our version of) [OSS Directory](https://github.com/opensource-observer/oss-directory): `@oso_entity_id('OSS_DIRECTORY', 'oso', 'my-project')`

It's extremely important to use these IDs consistently across models to ensure data integrity and consistency. The `@oso_entity_id` macro is used to generate these IDs deterministically.

### Events

Events represent actions or interactions that occur between entities. These can include things like commits, contract interactions, package imports, funding events, and more. Events are typically brought in from [public databases](../../integrate/datasets/index.mdx) via staging models.

We currently do not have a deterministic way to generate event IDs, but we are working on a solution to this problem. In the meantime, events are differentiated by their source, type, timestamp, and the to/from entities involved.

Some examples:

- A GitHub commit from a user to a repository
- A contract interaction from a user to a smart contract
- A dependency from a repo to an NPM package

Given that there are often billions of events associated with many of our sources, we typically aggregate these events into daily or monthly buckets for performance reasons.

### Metrics

Metrics are essentially aggregations of events over time for a specific entity type. These can include things like unique users, forks, funding amounts, and more. Metrics are generated using the `metrics_tools` package in SQLMesh so they can be applied consistently across different entity types and time periods. (Fun fact: this capability was one of the primary reasons we migrated our data pipeline to SQLMesh!)

In the future, we expect there to be many, many metrics. Therefore, we use a similar ID system to entities to ensure consistency and integrity, which is comprised of a source, namespace, and name. Metric names currently concatenate the event source, event type, and time period.

Some examples:

- GITHUB_releases_weekly, GITHUB_releases_daily, GITHUB_releases_over_all_time
- OPTIMISM_active_addresses_aggregation_daily, OPTIMISM_active_addresses_aggregation_over_90_day_period
- OPEN_COLLECTIVE_funding_received_monthly, OPEN_COLLECTIVE_funding_received_over_180_day_period

The power of this approach is that it allows us to easily compare metrics across different entity types and time periods, and to generate consistent cohorts and data visualizations. The (current) disadvantage is that you need to be precise when querying metrics to ensure you're getting the right data.

## Model Structure

### Hierarchy

Data models in OSO are organized in the `warehouse/oso_sqlmesh/models` directory, following these categories:

- **Staging (stg)**: Initial transformations that clean and standardize source data. There should be no joins or complex logic in staging models. A staging model should be able to run independently and feed everything downstream from it that requires the same source data.
- **Intermediate (int)**: Models that join and transform staging models into more complex structures. Intermediate models may contain aggregations or other complex logic. If you in doubt about where to put a model, it should probably be an intermediate model.
- **Mart**: Final models that are exposed to end users, typically containing registries, metrics, or aggregagated event data. We aim to have as few columns as possible in mart models to keep them performant. Marts models have versions postfixed with `_v0`, `_v1`, etc. Anything with a a `v0` is considered a development version and may be unstable.

In summary, staging models feed intermediate models, which feed mart models. When contributing new models, it's important to follow this structure to maintain consistency across the codebase.

## OSO ID System

OSO uses a consistent ID system across all entities in the data model. This system ensures that entities can be uniquely identified and related to each other across different data sources and models. Two key macros are used for generating IDs:

#### `@oso_id`

The `@oso_id` macro is used for generating IDs for other types of entities, particularly metrics and events. It typically takes two or three parameters:

```sql
@oso_id(source, namespace, name)
```

Examples from the OSO codebase:

```sql
-- For metrics
@oso_id('OSO', 'oso', metric) AS metric_id

-- For events
@oso_id(chain, '', transaction_hash) AS event_source_id

-- For issues
@oso_id(event_source, to_artifact_id, issue_number) AS issue_id
```

#### `@oso_entity_id`

The `@oso_entity_id` macro is used to generate a unique identifier for entities like artifacts, projects, collections, and users. It typically takes three parameters:

```sql
@oso_entity_id(source, namespace, name)
```

- **source**: The source system or platform (e.g., 'GITHUB', 'FARCASTER', 'OP_ATLAS')
- **namespace**: The namespace within the source (e.g., organization name for GitHub repositories)
- **name**: The specific name or identifier of the entity (e.g., repository name)

Examples from the OSO codebase:

```sql
-- For GitHub repositories
@oso_entity_id(event_source, to_artifact_namespace, to_artifact_name) AS to_artifact_id

-- For blockchain addresses
@oso_entity_id(chain, '', address) AS artifact_id

-- For users
@oso_entity_id('FARCASTER', '', fid) AS user_id

-- For projects
@oso_entity_id('OP_ATLAS', '', project_id) AS project_id

-- For collections
@oso_entity_id('OSS_DIRECTORY', 'oso', name) AS collection_id
```
