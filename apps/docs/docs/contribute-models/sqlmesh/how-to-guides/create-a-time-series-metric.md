---
title: Create a Time-Series Metric
sidebar_position: 2
---

:::info
This guide provides a focused walkthrough for creating a new time-series metric using OSO's metrics factory. This is one of the most common ways to contribute to OSO's data models.
:::

## Metrics Factory Overview

OSO has a framework in the `metrics_tools` directory for defining and calculating metrics across different entity types and time periods. This is done through a "metrics factory" that generates multiple, complex SQLMesh models from a simple SQL definition.

The process involves two main steps:

1.  **Create a Metric Definition**: A `.sql` file that defines the core logic of your metric.
2.  **Register the Metric**: An entry in the `metrics_factories.py` file that tells the factory how to generate the final models (e.g., what time aggregations to use).

### 1. Create a Metric Definition

Metric definitions are the `.sql` files that act as the starting point for generating metrics models. They contain the core SQL logic for calculating a single metric.

Here is an example of a metrics definition from the OSO codebase called `stars.sql`, which calculates the number of new stars a repository receives:

```sql
-- warehouse/oso_sqlmesh/oso_metrics/code/stars.sql
select
    @metrics_sample_date(events.bucket_day) as metrics_sample_date,
    events.event_source,
    events.to_artifact_id,
    '' as from_artifact_id,
    @metric_name() as metric,
    sum(events.amount) as amount
from oso.int_events_daily__github as events
where
    event_type in ('STARRED')
    and events.bucket_day between @metrics_start('DATE') and @metrics_end('DATE')
group by 1, metric, from_artifact_id, to_artifact_id, event_source
```

This query calculates the sum of `STARRED` events per day for each artifact. Note the use of special macros like `@metrics_sample_date`, `@metric_name`, `@metrics_start`, and `@metrics_end`. These are placeholders that the metrics factory will replace with the correct values for each generated model.

### 2. Register the Metric in the Factory

Once you have a metrics definition, you must register it in the `metrics_factories.py` file. This file is necessary to generate the final metrics models.

Here is an excerpt from the OSO codebase that registers the `stars` metric:

```python
# warehouse/oso_sqlmesh/models/metrics_factories.py
"stars": MetricQueryDef(
    ref="code/stars.sql",
    time_aggregations=["daily", "weekly", "monthly"],
    rolling=RollingConfig(
        windows=[30, 90, 180],
        unit="day",
        cron="@daily",
    ),
    entity_types=["artifact", "project", "collection"],
    over_all_time=True,
    metadata=MetricMetadata(
        display_name="Stars",
        description="Metrics related to GitHub stars",
    ),
    additional_tags=["data_category=code"],
),
```

Let's break down the key components:

- **`ref`**: The relative path to the metrics definition file.
- **`time_aggregations`**: The time aggregations to generate (e.g., `daily`, `weekly`, `monthly`).
- **`rolling`**: The rolling window configurations. The example above will generate 30, 90, and 180-day rolling aggregates.
- **`entity_types`**: The entity types for which to generate the metric (e.g., `artifact`, `project`, `collection`). The factory automatically handles the joins to these different entity types.
- **`over_all_time`**: A boolean that indicates whether to also generate a metric for the "all time" period.
- **`metadata`**: Metadata for the metric, including its display name and description.

### 3. Check the Rendered SQL

It is often useful to check the generated SQL for a given metrics model. To do this, OSO provides a command-line tool to render the SQL.

To see the generated SQL for the `stars` metric, you would run:

```bash
uv run oso metrics render stars
```

This will present a UI where you can choose which version of the generated model you'd like to see (e.g., `stars_to_artifact_weekly`, `stars_to_project_over_all_time`).

By default, this shows the "intermediate" SQL with some macros still present. To see the final, raw SQL that will be executed, you can specify a dialect:

```bash
uv run oso metrics render stars --full-render --dialect duckdb
```

This is an excellent way to debug your metric logic and understand how the factory works.
