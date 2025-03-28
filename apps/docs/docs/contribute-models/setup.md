---
title: Getting Started with SQLMesh
sidebar_position: 0
---

:::info
This guide will help you set up SQLMesh to contribute data models to OSO. SQLMesh is a powerful open-source SQL transformation framework that enables you to develop, test, and deploy SQL-based data transformations with confidence.
:::

## SQLMesh Overview

SQLMesh brings a version-controlled, plan-based approach to building data pipelines. It allows data teams to define transformations as SQL or Python models with a lightweight DSL, and manages the deployment of those models to your data warehouse or query engine in a consistent, reproducible way.

Key features of SQLMesh include:

- **Version-controlled snapshots**: Each model run produces a versioned table (snapshot) in a physical schema, and SQLMesh exposes a virtual layer of views for each environment (like dev or prod) pointing to the correct snapshot.
- **Isolated development environments**: Test changes in "zero-cost" virtual environments without copying data, and promote to production with confidence.
- **Semantic SQL understanding**: SQLMesh parses your SQL with the SQLGlot library, providing a semantic understanding of your queries (not just treating them as strings). This means it can catch errors like syntax issues or missing columns at compile time.
- **True incremental processing**: SQLMesh is incremental-first, keeping track of already-processed time ranges or keys and only processing new or changed data.
- **Built-in data consistency guards**: SQLMesh tracks the intervals of data each model has and prevents data gaps or overlaps, ensuring data integrity.

## Prerequisites

Before you begin, you'll need to have the following installed on your machine:

- [DuckDB](https://duckdb.org/) - A high-performance analytical database system
- Python 3.8 or higher
- Git (to clone the OSO repository)

## Installation

### Install DuckDB

DuckDB is required for local development and testing of SQLMesh models.

**macOS/Linux (using Homebrew):**

```bash
brew install duckdb
```

**Debian/Ubuntu (using APT):**

```bash
sudo apt-get install duckdb
```

### Clone the OSO Repository

If you haven't already, clone the OSO repository:

```bash
git clone https://github.com/opensource-observer/oso.git
cd oso
```

### Set Up Environment Variables

Create or update your `.env` file at the root of the OSO repository with the following variables:

```
GOOGLE_PROJECT_ID=opensource-observer
SQLMESH_DUCKDB_LOCAL_PATH=/tmp/oso.duckdb
```

### Authenticate with Google Cloud

SQLMesh needs access to Google Cloud to fetch data. Authenticate using:

```bash
gcloud auth application-default login
```

### Install Dependencies

Install the required Python dependencies:

```bash
uv sync
source .venv/bin/activate
```

## Initialize Local Data

To work with SQLMesh locally, you need to download playground data into your local DuckDB instance:

```bash
oso local initialize
```

This command will download the full dataset, which might be large. For a smaller sample, you can limit the data:

```bash
oso local initialize --max-results-per-query 10000 --max-days 7
```

Or using shortcuts:

```bash
oso local initialize -m 10000 -d 7
```

This will download 7 days of time series data with an approximate maximum of 10,000 rows in each table that is not time series defined.

## Running SQLMesh

### Test Your Setup

To verify that everything is set up correctly, run SQLMesh for a sample date range:

```bash
oso local sqlmesh plan dev --start 2025-03-01 --end 2025-03-31
```

This command uses a wrapper `oso local sqlmesh` that automatically uses the correct `warehouse/oso_sqlmesh` directory.

### Explore the Data

You can explore the data in DuckDB using the command line:

```bash
duckdb
```

Or specify the database path:

```bash
duckdb /tmp/oso.duckdb
```

Once in the DuckDB shell, you can see the available tables:

```sql
SHOW ALL TABLES;
```

And execute sample queries:

```sql
SELECT * FROM metrics__dev.metrics_v0 LIMIT 5;
```

## Testing Your Models

When developing new models, you can test them against your local DuckDB instance:

```bash
sqlmesh plan dev
```

For faster testing, you can specify a shorter date range:

```bash
sqlmesh plan dev --start 2024-12-01 --end 2024-12-31
```

## Adding New Data Sources

If a source that's in BigQuery is missing from DuckDB, you can add it to the `initialize_local_duckdb` function in `warehouse/metrics_tools/local/utils.py`.

Add new models as `TABLE_MAPPING` fields, for example:

```python
"opensource-observer.farcaster.profiles": "bigquery.farcaster.profiles",
```

Then reference the model in your SQLMesh code via `@oso_source('YOUR_MODEL')`.

**Important:** Whenever you add a new source, you will need to re-initialize your local database.

## Advanced Testing with Trino

While DuckDB is recommended for most development work, you can also test your models against a local Trino instance for more production-like validation.

### Using Docker Compose (Recommended)

This is the recommended way to test on Trino. It requires more resources than DuckDB but provides a more accurate representation of the production environment.

#### Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/install/)

Follow the instructions in the OSO repository to set up and run Trino with Docker Compose.

### Using Kubernetes with Kind

For advanced users who need to test with Kubernetes, you can set up a local Trino cluster using Kind.

#### Prerequisites

- [Docker](https://www.docker.com/)
- [Kind](https://kind.sigs.k8s.io/)
- Optional for debugging: [kubectl](https://kubernetes.io/docs/tasks/tools/) and [k9s](https://k9scli.io/topics/install/)

#### Setup

Initialize the local Trino cluster on Kubernetes:

```bash
oso ops cluster-setup
```

This can take approximately 10 minutes to complete. Once set up, you can check if Kind has started all your pods:

```bash
kubectl get pods --all-namespaces
kubectl get kustomizations --all-namespaces
```

Wait for all pods to come online, particularly `local-trino-psql`.

#### Initialize Trino Data

Initialize the local Trino with a smaller dataset:

```bash
oso local initialize --local-trino -m 1000 -d 3
```

#### Running SQLMesh with Trino

To run SQLMesh with your local Trino instance:

```bash
oso local sqlmesh --local-trino plan
```

The `--local-trino` option should be passed before any SQLMesh arguments.

#### Debugging Trino

You can expose your local Trino instance for debugging:

```bash
kubectl port-forward --namespace=local-trino service/local-trino-trino 8080:8080 --address 0.0.0.0
```

This will open a web server to interact with Trino directly at `http://127.0.0.1:8080`.

## Next Steps

Now that you have SQLMesh set up, you're ready to start contributing data models to OSO. Check out the [Data Models](./data-models.md) guide to learn how to create and contribute models.
