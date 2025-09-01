---
title: dbt Setup
sidebar_position: 7
---

:::warning
We are in the process of deprecating our dbt setup in favor of sqlmesh.
We have left the dbt setup in case there are models we still need to run
manually.
:::

We use dbt to run a BigQuery-based data pipeline.
You can view every dbt model on OSO here:
[https://models.opensource.observer](https://models.opensource.observer/).

This guide walks you through setting up dbt (Data Build Tool) for OSO development.

## Prerequisites

- Python >=3.11 (see [here](https://www.python.org/downloads/))
- Python uv >= 0.6 (see [here](https://pypi.org/project/uv/))
- git (see [here](https://github.com/git-guides/install-git))
- A GitHub account
- BigQuery access
- `gcloud` CLI (see [here](https://cloud.google.com/sdk/docs/install))

### Setup dependencies

1. Activate the virtual environment:

```bash
source .venv/bin/activate
```

2. Verify dbt is installed:

```bash
which dbt
```

3. Authenticate with gcloud:

```bash
gcloud auth application-default login
```

4. Run the setup wizard:

```bash
uv sync && uv run oso_lets_go
```

:::tip
The script is idempotent, so you can safely run it again
if you encounter any issues.
The wizard will create a GCP project and BigQuery dataset if needed, copy a subset of OSO data for development, and configure your dbt profile.
:::

## Configuration

### dbt Profile Setup

Create or edit `~/.dbt/profiles.yml`:

```yaml
opensource_observer:
  outputs:
    production:
      type: bigquery
      dataset: oso
      job_execution_time_seconds: 300
      job_retries: 1
      location: US
      method: oauth
      project: opensource-observer
      threads: 32
    playground:
      type: bigquery
      dataset: oso_playground
      job_execution_time_seconds: 300
      job_retries: 1
      location: US
      method: oauth
      project: opensource-observer
      threads: 32
  target: playground
```

### VS Code Setup

1. Install the [Power User for dbt core](https://marketplace.visualstudio.com/items?itemName=innoverio.vscode-dbt-power-user) extension

2. Get your virtual environment path:

```bash
echo 'import sys; print(sys.prefix)' | uv run -
```

3. In VS Code:
   - Open command palette
   - Select "Python: select interpreter"
   - Choose "Enter interpreter path..."
   - Enter the virtual path

## Running dbt

Basic usage:

```bash
dbt run
```

Target specific model:

```bash
dbt run --select {model_name}
```

:::tip
By default, this writes to the `opensource-observer.oso_playground` dataset.
:::

You can view all of our models and their documentation at [https://models.opensource.observer](https://models.opensource.observer/).

## Model Organization

Our dbt models are located in `warehouse/dbt/models/` and follow these conventions:

- `staging/` - Extract raw source data with minimal transformation (usually materialized as views)
- `intermediate/` - Transform staging data into useful representations
- `marts/` - Final aggregations and metrics (copied to frontend database)

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

## FAQ

### Defining a dbt source

In order to make a new dataset available to the data pipeline,
you need to add it as a dbt source.
In this example, we create a source in `oso/warehouse/dbt/models/`
(see [source](https://github.com/opensource-observer/oso/blob/main/warehouse/dbt/models/ethereum_sources.yml))
for the Ethereum mainnet
[public dataset](https://cloud.google.com/blog/products/data-analytics/ethereum-bigquery-public-dataset-smart-contract-analytics).

```yaml
sources:
  - name: ethereum
    database: bigquery-public-data
    schema: crypto_ethereum
    tables:
      - name: transactions
        identifier: transactions
      - name: traces
        identifier: traces
```

We can then reference these tables in downstream models with
the `source` macro:

```sql
select
  block_timestamp,
  `hash` as transaction_hash,
  from_address,
  receipt_contract_address
from {{ source("ethereum", "transactions") }}
```

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

### Working with IDs

Use the `oso_id()` macro to generate consistent identifiers across our data models. This macro creates a URL-safe base64 encoding of a SHA256 hash of the concatenated input parameters.

For example, to generate an artifact ID:

```sql
{{ oso_id("artifact_source", "artifact_source_id") }}
```

## Reference Documentation

- Browse models: [`warehouse/dbt/models`](https://github.com/opensource-observer/oso/tree/main/warehouse/dbt/models)
- Online docs: [models.opensource.observer](https://models.opensource.observer/)
