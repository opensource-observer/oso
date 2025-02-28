---
title: dbt Setup
sidebar_position: 5
---

We use dbt to build our data warehouse. You can view every model on OSO here: [https://models.opensource.observer](https://models.opensource.observer/).

This guide walks you through setting up dbt (Data Build Tool) for OSO development.

## Prerequisites

- Python >=3.11
- Python uv >= 0.6
- git
- A GitHub account
- BigQuery access
- `gcloud` CLI

### Installing gcloud CLI

For macOS users:

```bash
brew install --cask google-cloud-sdk
```

For other platforms, follow the [official instructions](https://cloud.google.com/sdk/docs/install).

## Installation

1. Follow the installation instructions in our monorepo [README](https://github.com/opensource-observer/oso).

2. Activate the virtual environment:

```bash
source .venv/bin/activate
```

3. Verify dbt is installed:

```bash
which dbt
```

4. Authenticate with gcloud:

```bash
gcloud auth application-default login
```

5. Run the setup wizard:

```bash
uv sync && uv run oso_lets_go
```

:::tip
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

For more details on working with dbt models, see our [Data Models Guide](../contribute-models/data-models.md).
