# OSO sqlmesh pipeline

## Setup

Make sure to set the following environment variables
in your .env file (at the root of the oso repo)

```
GOOGLE_PROJECT_ID=opensource-observer
SQLMESH_DUCKDB_LOCAL_PATH=/tmp/oso.duckdb
```

Make sure you've logged into Google Cloud on your terminal

```bash
gcloud auth application-default login
```

Now install dependencies and download playground data into
a local DuckDB instance.

```bash
poetry install
poetry shell
oso metrics local initialize
```

## Run

```bash
cd warehouse/metrics_mesh
sqlmesh plan dev --start 2024-07-01 --end 2024-08-01 # to run for specific date rates (fast)
sqlmesh plan  # to run the entire pipeline (slow)
```
