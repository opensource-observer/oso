---
title: Contribute SQL Models
sidebar_position: 5
---

:::info
[dbt](https://www.getdbt.com/blog/what-exactly-is-dbt) enables data analysts and engineers to transform data in OSO's warehouse using SQL. We use it to define impact metrics and materialize aggregate data about projects.
:::

You can view all of our models and their documentation at [https://models.opensource.observer](https://models.opensource.observer/).

Before starting, make sure you've completed the [dbt setup guide](../guides/dbt.md) and followed the installation instructions in our monorepo [README](https://github.com/opensource-observer/oso).

## Model Organization

Our dbt models are located in `warehouse/dbt/models/` and follow these conventions:

- `staging/` - Extract raw source data with minimal transformation (usually materialized as views)
- `intermediate/` - Transform staging data into useful representations
- `marts/` - Final aggregations and metrics (copied to frontend database)

## Data Sources

### Referring to Data Sources in Intermediate and Marts Models

All intermediate and mart models should refer to data sources using the `ref()` macro.

For example, to refer to staged data from the `github_archive` source, you can use:

```sql
{{ ref('stg_github__events') }}
```

And to refer to data from the `int_events` intermediate model, you can use:

```sql
{{ ref('int_events') }}
```

### Referring to Data Sources in Staging Models

Staging models can refer to data sources using the `source()` macro.

For example, to refer to raw data from the `github_archive` source, you can use:

```sql
{{ source('github_archive', 'events') }}
```

### The `oso_source` macro

Use `oso_source()` instead of `source()` to help manage our playground dataset:

```sql
{{ oso_source('namespace', 'table_name') }}
```

## Working with IDs

Use the `oso_id()` macro to generate consistent identifiers across our data models. This macro creates a URL-safe base64 encoding of a SHA256 hash of the concatenated input parameters.

For example, to generate an artifact ID:

```sql
{{ oso_id("artifact_source", "artifact_source_id") }}
```

## Development Workflow

1. **Write Your Model**

   - Add SQL files to appropriate directory in `warehouse/dbt/models/`
   - Use existing models as references

2. **Test Locally**

   ```bash
   dbt run --select your_model_name
   ```

   By default, this will run the `oso_playground` dataset. If you want to run against the production dataset, you can use the `--target` flag:

   ```bash
   dbt run --select your_model_name --target production
   ```

   You can also run all models downstream of a given model by appending a `+` to the model name:

   ```bash
   dbt run --select your_model_name+
   ```

3. **Using BigQuery UI**

   ```bash
   dbt compile --select your_model_name
   ```

   Find compiled SQL in `target/` directory to run in [BigQuery Console](https://console.cloud.google.com/bigquery)

   Alternatively, you can used the `pbcopy` command to copy the SQL to your clipboard:

   ```bash
   dbt compile --select your_model_name | pbcopy
   ```

4. **Submit PR**
   - Models are deployed automatically after merge to main
   - Monitor runs in Dagster UI: [https://dagster.opensource.observer](https://dagster.opensource.observer)

## Reference Documentation

- Browse models: [`warehouse/dbt/models`](https://github.com/opensource-observer/oso/tree/main/warehouse/dbt/models)
- Online docs: [models.opensource.observer](https://models.opensource.observer/)
