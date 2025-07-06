---
title: Time Series Metrics Factory Deep Dive
sidebar_position: 1
---

:::info
This guide is for an in-depth understanding of our model generation
factory that is used to generate the time series metrics for OSO. If you'd like
a more practical example of how to add new time series metrics models, [go
here](./data-models.md).
:::

## Background

The creation of the time series metrics factory requires some deeper knowledge
about sqlmesh and sqlglot. Much of this information is available in the
documentation for sqlmesh and sqlglot but the combined utility is not readily
documented. This section covers an overview of prerequisite knowledge:

### SQLMesh Python Models

The timeseries metrics generation take advantage of the fact that sqlmesh allows
for python models as well as sql models. A python model in sqlmesh looks
something like this:

```python
import typing as t
from datetime import datetime

from sqlmesh import ExecutionContext, model

@model(
    "my_model.name",
    columns={
        "column_name": "int",
    },
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> pd.DataFrame:
    ...
```

According to the sqlmesh documentation, Python models come in two different
forms:

1. A model that returns a dataframe (e.g. pandas, pyspark, snowpark)
2. A model that returns a sqlglot expression (`sqlglot.exp.Expression`)

These models are discovered by sqlmesh's loader as long as the model exists in
the `models` directory of a sqlmesh project.

### Python Models and Factory Functions

Since python models are simply python code the sqlmesh loader will simply
execute any python modules in the `models` directory. This then allows for a
factory pattern with regards to sqlmesh python models. This is a basic example:

```python
def model_factory(values: list[str]):
    @model(
        f"my_model.{values}_model",
        columns={
            "column_name": "int",
        },
    )
    def execute(
        context: ExecutionContext,
        start: datetime,
        end: datetime,
        execution_time: datetime,
        **kwargs: t.Any,
    ) -> pd.DataFrame:
        ...

```

In this example, the factory takes an input of `values` which is just a list of
strings. If Used like this:

```python
# Instantiate the factory
model_factory(["foo", "bar", "baz"])
```

We would then generate `my_model.foo_model`, `my_model.bar_model`, and
`my_model.baz_model`.

This contrived example isn't all that useful but if you can imagine that the
`values` parameter could be derived in any way that python allows, it opens up
possibilities. On its own this might not seem useful but this pattern is the
building block of the time series metrics factory.

### SQLGlot Rewriting

With the timeseries metrics factory we take advantage of the fact that sqlglot
can handle semantic rewriting to do some fairly powerful transformations for
when generating metrics models. Take for example the following sql:

```python
SELECT e.id as id, e.name as name FROM employees as e
```

When parsed by SQLGlot using `sqlglot.parse_one` we get the following AST.

```python
Select(
  expressions=[
    Alias(
      this=Column(
        this=Identifier(this=id, quoted=False),
        table=Identifier(this=e, quoted=False)),
      alias=Identifier(this=id, quoted=False)),
    Alias(
      this=Column(
        this=Identifier(this=name, quoted=False),
        table=Identifier(this=e, quoted=False)),
      alias=Identifier(this=name, quoted=False))],
  from=From(
    this=Table(
      this=Identifier(this=employees, quoted=False),
      alias=TableAlias(
        this=Identifier(this=e, quoted=False)))))
```

Given this object representation, we can actually use sqlglot to rewrite the
source_table to point to an entirely different source table. If we wished to
instead use `updated_employees` as the source table, that's something we can do
like this:

```python
from sqlglot import parse_one, exp

query = parse_one("SELECT e.id as id, e.name as name FROM employees as e")
updated_table_name_query = exp.replace_tables(query, {"employees": "updated_employees"})
```

More interestingly, let's say we wanted to use the `employees` but instead of
getting just the `id` of a given employee in the `source_table` we also want to
get the department name by joining on the departments table. Let's pretend that
the employees table also has `department_id` as an available column.

We could do this transform as follows:

```python
# The top level expression is a `sqlglot.exp.Select` expression.
# This has the columns in the `expressions` property. Ideally,
# we'd actually want to wrap this in a function that doesn't update
# this in place so we can preserve the original query, but for simplicity
# we simply do this for now.
query.expressions.append(exp.to_column("d.department_name").as_("department_name"))

# To add the join we simply add it to the parsed object.
# Notice we need to have query on the left side of the equal sign.
# This is because the `join()` method does not update the original
# object in place.
query = query.join(
    exp.to_table("departments").as_("d"),
    on="d.department_id = e.department_id",
    join_type="inner"
)
```

And this would generate the following SQL:

```sql
SELECT
  e.id AS id,
  e.name AS name,
  d.department_name AS department_name
FROM employees AS e
INNER JOIN departments AS d
  ON d.department_id = e.department_id
```

## Time Series Metrics Factory Overview

Our time series metrics factory has been enhanced to offer even greater flexibility and precision. This factory function generates a collection of models based on configurations that parameterize any query performing aggregation. The parameterizations now cover not only entity relationships and standard time aggregations (e.g., daily, weekly), but also advanced rolling windows and custom transformations powered by SQLGlot.

### Key Enhancements

- **Granularity Control**: Added support for configurable grain levels in rolling windows and aggregation intervals (e.g., `weekly` or `monthly`).
- **Custom Entity Relationships**: Improved handling of complex joins for multi-entity metrics definitions.
- **Macro Injection**: Expanded macro library with new functions to streamline time boundary calculations and metadata tagging.
- **Dynamic Query Rendering**: Leveraging SQLGlot for advanced query transformations, including conditional joins and derived columns.

By adopting these enhancements, the time series metrics factory reduces maintenance overhead, ensures consistency across models, and enables complex analysis with minimal code duplication.

### Expanded Use of Macros

Building on existing macros like `@metrics_sample_date` and `@metrics_peer_ref`, the factory now supports additional macro functions for granular control and dynamic transformations:

- **`@metrics_grain`**: Dynamically adjusts the grain level for queries based on configuration parameters.
- **`@entity_relationships`**: Resolves complex multi-entity relationships and generates the appropriate joins automatically.
- **`@rolling_window_offset`**: Calculates offsets for rolling window comparisons between metrics.

These macros are injected into each generated model, ensuring seamless integration with SQLMesh's execution framework.

## Workflow for Adding Metrics

To illustrate the new capabilities, here's an example of adding a GitHub stars metric:

**1. Write the SQL**

```sql
SELECT
  @metrics_sample_date(events.bucket_day) AS metrics_sample_date,
  events.event_source,
  events.to_artifact_id,
  '' AS from_artifact_id,
  @metric_name() AS metric,
  SUM(events.amount) AS amount
FROM oso.int_events_daily__github AS events
WHERE
  event_type IN ('STARRED')
  AND events.bucket_day BETWEEN @metrics_start('DATE') AND @metrics_end('DATE')
GROUP BY 1, metric, from_artifact_id, to_artifact_id, event_source
```

**2. Define the Metric Query**

```python
"stars": MetricQueryDef(
    ref="code/stars.sql",
    time_aggregations=["daily", "monthly", "quarterly"],
    rolling=RollingConfig(
        windows=[30, 90, 180],
        unit="day",
        cron="@daily",
    ),
    entity_types=["artifact", "project", "collection"],
    metadata=MetricMetadata(
        display_name="GitHub Stars",
        description="Aggregates GitHub stars across repositories and projects.",
    ),
),
```

**3. Render the Queries**

```bash
uv run oso metrics render stars --full-render --dialect duckdb
```

This generates SQL for each combination of entity type and aggregation interval, leveraging the advanced macros for dynamic grain adjustments and relationships.

**4. Validate the Models**:

Run the models locally to ensure correctness:

```bash
uv run oso local sqlmesh-test --duckdb plan dev --start '1 week' --end now
```

**5. Submit the Changes**:

Push to GitHub and create a pull request following the established workflow.

By following this process, you can efficiently integrate new metrics while maintaining consistency across the OSO data pipeline.

## Conclusion

The updated time series metrics factory streamlines the creation of robust, scalable models for OSO. By leveraging SQLMesh and SQLGlot's advanced capabilities, you can define metrics with precision and flexibility. For more practical examples, refer to the [data models guide](./data-models.md).

Happy modeling!
