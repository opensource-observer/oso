---
title: Model Configuration
sidebar_position: 1
---

:::info
This guide provides a detailed reference for configuring SQLMesh models in OSO, including naming conventions, materialization strategies, partitioning, and grain settings.
:::

## Naming Conventions

Note that SQLMesh ignores folders, so the model name must be uniqe and should be descriptive enough to indicate its category. In addition, when naming your models, try to follow these conventions:

- **Use the Correct Prefix**: Prefix your model name with `stg_` or `int_` to indicate the category. Mart models should not have prefixes but should end with a version number (eg, `_v0`, `_v1`)
- **Use Descriptive Names**: Choose names that clearly indicate the model's purpose and source data.
- **Use Underscores**: Separate words in the model name with underscores for readability. Use two underscores to separate the category from the model name (eg, `stg_github__commits.sql`).

## Materialization Strategies

SQLMesh supports several types of models with different materialization strategies:

- **FULL**: A complete table that is rebuilt from scratch on each run. This is the simplest type but can be inefficient for large datasets.
- **INCREMENTAL_BY_TIME_RANGE**: Models that process data in time-based chunks. These are ideal for event data where you want to process new time periods incrementally.
- **INCREMENTAL_BY_UNIQUE_KEY**: Models that perform upserts based on a unique key. These are useful for dimension tables or slowly changing data.
- **INCREMENTAL_BY_PARTITION**: Models that process data in discrete partitions. These are useful when data must be processed in static groupings like `event_source` or ID ranges.

Most models in OSO use either the `FULL` or `INCREMENTAL_BY_TIME_RANGE` strategy.

## Incrementing and Partitioning

Large event models should be partitioned and processed incrementally in order to keep compute costs manageable. When doing this, it is important to ensure that any upstream models are also partitioned and incremental. If an incremental model depends on a non-incremental model that is changing frequently, then your model may have some data integrity issues (or will need to be rebuilt frequently, which defeats the purpose of making it incremental).

Here's an example of an intermediate model from the OSO codebase:

```sql
MODEL (
  name oso.int_events_daily__github,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 365,
    batch_concurrency 1
  ),
  start @github_incremental_start,
  cron '@daily',
  partitioned_by (DAY("bucket_day"), "event_type"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id)
);

SELECT
  DATE_TRUNC('DAY', time::DATE) AS bucket_day,
  from_artifact_id::VARCHAR AS from_artifact_id,
  to_artifact_id::VARCHAR AS to_artifact_id,
  event_source::VARCHAR,
  event_type::VARCHAR,
  SUM(amount::DOUBLE)::DOUBLE AS amount
FROM oso.int_events__github as events
WHERE time BETWEEN @start_dt AND @end_dt
GROUP BY
  DATE_TRUNC('DAY', time::DATE),
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type
```

### Incremental Settings

In the above example, there are several key settings to note:

- `kind=INCREMENTAL_BY_TIME_RANGE` specifies that this is an incremental model based on time
- `time_column="bucket_day"` indicates which column contains the timestamp for incremental processing
- `@github_incremental_start` is a global variable that defines the start date for incremental processing for this source
- `@start_date` and `@end_date` are automatically set by SQLMesh to the appropriate time range for each run

### Partition Settings

The example above also includes a `partitioned_by` tuple:

```sql
partitioned_by (DAY("bucket_day"), "event_type"),
```

The `DAY` in `DAY("bucket_day")` is Trino's date trunc syntax, i.e., ensuring the `bucket_day` column is date truncated.

It's important to be thoughtful about how you partition your tables. In general, you should partition by the columns you most frequently filter on in your queries. If you make your partitions too granular, you may end up with too many small files, which can slow down queries. If you make them too large, you may not get the performance benefits of partition pruning.

### Grain Settings

The `grain` setting is used by SQLMesh to define the unique key(s) for the model. It is basically a composite key that ensures the model is unique at the grain level. This is important for ensuring data integrity and consistency across models. In the example above, the grain is defined as:

```sql
grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id)
```

If you configure your grain right, then SQLMesh can intelligently determine what data needs to be updated in the model. If you get it wrong (e.g., you forget to include a column that is part of the unique key), then you may end up with data integrity issues. If you ignore the grain, then SQLMesh will assume you want to rebuild the entire model each time, which can be very inefficient for large models.
