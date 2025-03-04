# OSO sqlmesh pipeline

## Setup

You will need [DuckDB](https://duckdb.org/) on your machine.

Install using Homebrew (macOS/Linux):

```bash
brew install duckdb
```

Install using APT (Debian/Ubuntu):

```bash
sudo apt-get install duckdb
```

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

Now install dependencies.

```bash
uv sync
source ../../.venv/bin/activate
```

Finally, download playground data into your local DuckDB instance with the following command

```bash
oso local initialize
```

Or to take a smaller sample:

```bash
oso local initialize --max-results-per-query 10000 --max-days 7
```

Or using shortcuts:

```bash
oso local initialize -m 10000 -d 7
```

## Run

Run sqlmesh for a sample date range:

```bash
oso local sqlmesh plan dev --start 2024-07-01 --end 2024-08-01 # to run for specific date rates (fast)
# sqlmesh plan # to run the entire pipeline (slow)
```

_Note, the command above uses a wrapper `oso local sqlmesh` that will
automatically use the correct `warehouse/oso_sqlmesh` directory. It can also be
used to run with a local trino (see below)._

Explore the data in DuckDB:

```bash
duckdb
```

or

```bash
duckdb /tmp/oso.duckdb
```

See the tables are loaded:

```bash
SHOW ALL TABLES;
```

Execute a sample query:

```sql
SELECT * FROM metrics__dev.metrics_v0 LIMIT 5;
```

## Testing

Compile against your local DuckDB copy by running:

```bash
sqlmesh plan dev
```

As this will run against everything in the dataset, you may want to pick a shorter date range (that you know has data in it), eg:

```bash
sqlmesh plan dev --start 2024-12-01 --end 2024-12-31
```

If a source that's in BigQuery is missing from DuckDB, check the `initialize_local_duckdb` function in [utils.py](warehouse/metrics_tools/local/utils.py).
You can add new models as `bq_to_duckdb` parameters, eg:

```python
"opensource-observer.oso_playground.YOUR_MODEL": "sources.YOUR_MODEL",
```

...and then reference the model in your sqlmesh code via `@oso_source('YOUR_MODEL')`.

Important: whenever you add a new source, you will need to re-initialize your local database:

```bash
oso local initialize
```

Then you can run to compile the latest models:

```bash
oso local sqlmesh plan dev
```

And if it executes successfully, view it in DuckDB:

```sql
SELECT * FROM metrics__dev.YOUR_MODEL LIMIT 5;
```

## Sqlmesh Wrapper

This is a convenience function for running sqlmesh locally. This is equivalent
to running this series of commands:

```bash
cd warehouse/oso_sqlmesh
sqlmesh [...any sqlmesh args... ]
```

So running:

```bash
oso local sqlmesh plan
```

Would be equivalent to

```bash
cd warehouse/oso_sqlmesh
sqlmesh plan
```

## Running sqlmesh on a local trino

Be warned, running local trino requires running kubernetes on your machine using
[kind](https://kind.sigs.k8s.io/). While it isn't intended to be a heavy weight
implementation, it takes more resources than simply running with duckdb. For
this reason alone, we suggest most initial testing to happen on duckdb. However,
in order to simulate and test this running against trino as it does on the
production OSO deployment, we need to have things wired properly with
kubernetes.

### Prerequisites

In addition to having the normal dev tools for running the repo, you will also need:

- [docker](https://www.docker.com/)
- [kind](https://kind.sigs.k8s.io/)

Please install these before continuing.

For debugging, you may also want to install:

- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [k9s](https://k9scli.io/topics/install/)

### Local Kubernetes Cluster Setup

To initialize everything simply do:

```bash
oso ops cluster-setup
```

This can take a while so please be patient, but it will generate a local
registry that is used when running the trino deployment with the metrics
calculation service deployed. This is to test that process works and to ensure
that the MCS has the proper version deployed. Eventually this can/will be used
to test the dagster deployment.

_Note: It will probably look like it's stuck at the `Build and publish docker
image to local registry` step._

Once everything is setup, things should be running in the kind cluster
`oso-local-test-cluster`. Normally, you'd need to ensure that you forward the
right ports so that you can access the cluster to run the sqlmesh jobs but the
convenience functions we created to run sqlmesh ensure that this is done
automatically. However, before running sqlmesh you will need to initialize the
data in trino.

You can check if Kind has started all your pods:

```bash
kubectl get pods --all-namespaces
kubectl get kustomizations --all-namespaces
```

It may take an additional ~10 minutes after `oso ops cluster-setup` for
all the pods to come online.
In particular, you are waiting for `local-trino-psql` to be in a
"Running" state before you can run the data initialization.

If you need to kill your Kind cluster and start over, you can run

```bash
kind delete cluster --name oso-local-test-cluster
```

### Initialize Trino Data

Much like running against a local duckdb the local trino can also be initialized
with on the CLI like so:

```bash
oso local initialize --local-trino -m 1000 -d 3
```

_Note: It's best not to load too much data into trino for local testing. It won't be as
fast as sqlmesh with duckdb locally._

Once initialized, trino will be configured to have the proper source data for
sqlmesh.

### Running `plan` or `run`

Finally, to run `sqlmesh plan` do this:

```bash
oso local sqlmesh --local-trino plan
```

The `--local-trino` option should be passed before any sqlmesh args. Otherwise,
you can call any command or use any flags from sqlmesh after the `sqlmesh`
keyword in the command invocation. So to call `sqlmesh run` you'd simply do:

```bash
oso local sqlmesh --local-trino run
```

### Changing branches or random logouts

Please note, you may periodically be logged out of the local kind cluster or you
will need to change branches that you'd like the cluster to use. Just run `oso
ops cluster-setup` again and it will properly update the local cluster. It could
take a few minutes for the cluster to synchronize to the declared configuration.

### Debugging Trino

You can expose your local Trino instance for debugging by running:

```bash
kubectl port-forward --namespace=local-trino service/local-trino-trino 8080:8080 --address 0.0.0.0
```

This will open up a web server to interact with Trino directly at
`http://127.0.0.1:8080`.

## Metrics Overview

Metrics are generated using the tools in `metrics_tools`.

### Essential Concepts

- Metrics Definition
  - These are the `.sql` files that act as the starting point for generating
    metrics models. The metrics models are generated by taking taking all
    permutations of aggregation intervals and entity types for the given metric.
    At this time this isn't a fully generic semantic model but is a pragmatic
    approximation for the OSO use case.
- Metric Types
  - _time aggregation_ - This is an aggregation that operates by aggregating
    within a specific bucket of time. We may sometimes call this a "normal"
    aggregation
  - _rolling window aggregation_ - These are aggregations that look back some
    user defined number of days at an interval specified by a `cron` parameter
    in a rolling fashion. So if you have a 30 day rolling window with a daily
    cron, the final table is generated by iterating through each day and
    aggregating the previous 30 days of each day.
- Entity Types
  - These are related to the OSO entities artifact, project and collection. The
    default entity type is artifact and _every_ metric model should be written,
    for now, as if the aggregation is operating on just an artifact.
- Metric Time Range
  - Regardless of the aggregation type the metrics will be passed in start/end times in the form of a custom sqlmesh macro (described below). These start/end times are based on the rolling window or the time aggregation. If the rolling window i

## Metrics Special Macros

### `@metrics_peer_ref`

Reference a different metrics table that is being generated by the timeseries
metrics factory. This should only be used if the table dependency is also
defined in the same factory.

#### Parameters

- `name` - The name of the table dependency
- `entity_type` - _optional_ - The entity type for the current peer reference.
  Defaults to the entity type used in the current metric
- `window` - _optional_ - The size of the table dependency's window. If
  `time_aggregation` is not set, this and `unit` must be set.
- `unit` - _optional_ - The unit of the table dependency's window. If
  `time_aggregation` is not set, this and the `window` must be set.
- `time_aggregation` - _optional_ - The time aggregation used (one of `daily`,
  `weekly`, `monthly`). If this is not set then `window` and `unit` must be set.

_NOTE: Optional parameters should use the "kwargs" syntax in sqlmesh dialect.
This looks like `key := 'value'`_

#### Example

Select star from a dependent table that matches the current rolling window settings:

```sql
SELECT *
-- As noted in the docs the `entity_type` is inferred from the settings on this metric
FROM @metrics_peer_ref(`dep`, window := @rolling_window, unit := @rolling_unit)
```

Select star from a dependent table that matches the current time aggregation
settings, but only for the `artifact` entity type.

```sql
SELECT *
FROM @metrics_peer_ref(`dep`, entity_type := 'artifact', time_aggregation := @time_aggregation)
```

### `@metrics_sample_date`

Derives the correct sample date for a metric based on the metric type (normal
aggregation or rolling window aggregation). This is essential to use for first
order metrics.

Usage:

```
@metrics_sample_date(event_table_source.event_table_date_column)
```

The passed in date should be the date column of a given time series event
source. In all cases that must use this, this is just
`int_events_daily_to_artifact.bucket_day`.

### `@metric_start` and `@metric_end`

For rolling windows or time aggregations that have boundaries that correlate to
times, these provide the proper time ranges. So for a rolling window of 30 days
this will give a 30 day time window where the start days is 30 days _before_ the
interval for the current increment of the given model. So for example if the
increment is `2024-01-30` the start will be `2024-01-01` and the end will be
`2024-01-30`. These macros take a single argument which is the data type to use
for the returned value.

Usage:

For a date

```
@metrics_start(DATE)
```

For a timestamp (the value you use for type will depend on the dialect you're
using)

```
@metrics_start(TIMESTAMP)
```

### `@metrics_name`

The metrics name is used to generate a name for a given metric. By default this
can be used without any arguments and the metrics model factory will
automatically assign a metric name. However in cases like the developer
classifications we want to create multiple types of metrics in a given query. We
can accomplish simply using this macro. The first argument is the "prefix" name
of the metric. This macro will then generate the appropriate suffix. For time
aggregations this will simply be something like `daily`, `weekly`, or `monthly`.
For rolling windows this will be something like, `_over_30_days` or
`_over_3_months` (the exact string depends on the rolling window configuration).

### `@metrics_entity_type_col`

Provides a way to reference the generated column for a given entity type in a
metrics model. This is required because the metrics definition only acts as the
starting point of a metric from the perspective of an artifact. To get metrics
for projects and collections we need this macro while we aren't doing a fully
generic semantic model. be entity column name based on the currently queried
entity type. When queries are being automatically generated, entity types are
changed so the column used to reference the entity column also changes. This
macro allows for the queries to succeed by accepting a format string where the
variable `entity_type` referenced as `{entity_type}` in the format string is
interpreted as the current entity type (`artifact`, `project`, `collection`).

Usage:

```
@metrics_entity_type_col("to_{entity_type}_id")
```

If a query uses like so:

```
SELECT
  @metrics_entity_type_col("to_{entity_type}_id", t)
FROM table as t
```

The following SQL would be rendered for different entity types (the joins are
approximated for example only)

Artifact:

```
SELECT
  t.to_artifact_id
FROM table as t
```

Project:

```
SELECT
  artifact_to_project.project_id as to_project_id
FROM table as t
JOIN artifact_to_project as artifact_to_project
  ON artifact_to_project.artifact_id = t.to_artifact_id
```

Collection

```
SELECT
  project_to_collection.collection_id as to_collection_id
FROM table as t
JOIN artifact_to_project as artifact_to_project
  ON artifact_to_project.artifact_id = t.to_artifact_id
JOIN project_to_collection as project_to_collection
  ON project_to_collection.to_project_id = artifact_to_project.to_project_id

```

### `@metrics_entity_type_alias`

Like, `@metric_entity_type_col` but programmatically aliases any input
expression with one that derives from the entity type.

Usage:

```
@metrics_entity_type_alias(some_column, 'some_{entity_type}_column")
```

### `@relative_window_sample_date`

_WARNING: Interface likely to change_

Gets a rolling window sample date relative to the a passed in base date. This is
intended to allow comparison of multiple rolling intervals to each other. This
doesn't specifically use the rolling window parameters of a table dependency
(that will likely change in the future), but is instead just a convenience
function to calculate the correct dates that would be used to make that rolling
window comparison. We calculate a relative window's sample date using this
formula:

```
$base + INTERVAL $relative_index * $window $unit
```

_Note: The dollar sign `$` is used here to signify that this is a parameter in the above
context_

Inherently, this won't, for now, work on custom unit types as the interval must
be a valid SQL interval type. Also note, the base should almost _always_ be the
`@metrics_end` date.

#### Parameters

- `base` - The date time to use as the basis for this relative sample date
  calculation
- `window` - The rolling window size of the table we'd like to depend on
- `unit` - The rolling window unit of the table we'd like to depend on
- `relative_index` - The relative index to the current interval. This allows us
  to look forward or back a certain number of rolling intervals in an upstream
  table.

#### Examples

To get the date for the current, the last, and the second to last sample date of
a 90 day rolling window, you could do the following:

```sql
SELECT
  -- Relative index 0. This just becomes 2024-01-01
  @relative_window_sample_date('2024-01-01', 90, 'day', 0)
  -- Relative index -1. This becomes 2023-10-03
  @relative_window_sample_date('2024-01-01', 90, 'day', -1)
  -- Relative index -2. This becomes 2023-07-05
  @relative_window_sample_date('2024-01-01', 90, 'day', -2)
```
