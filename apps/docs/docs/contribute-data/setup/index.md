---
title: Getting Started with Dagster
sidebar_position: 0
---

[Dagster](https://dagster.io) is a modern data orchestrator that we use to declare
all data assets in software. OSO uses it to schedule all data jobs,
from data collectors to our transformation pipeline.
This quickstart guide will help you set
up a development Dagster instance locally, with a [`duckdb`](http://duckdb.org/) backend,
in order to follow along with our tutorials in the next sections.

If you want to check out what Dagster looks like in production, check out
[https://dagster.opensource.observer](https://dagster.opensource.observer)
Admins can trigger runs
[here](https://admin-dagster.opensource.observer/)

## Setting up Dagster

First, we need to clone the
[OSO monorepo](http://github.com/opensource-observer/oso) and install
the required dependencies using
[uv](https://docs.astral.sh/uv/):

```sh
git clone git@github.com:opensource-observer/oso.git
cd oso/
uv sync
```

Create a directory to store Dagster state. It is safe to delete this directory,
so we typically store this in `/tmp`.

```sh
mkdir /tmp/dagster-home
```

Copy `.env.example` to `.env`, and fill it in with the required environment variables:

```sh
DAGSTER_HOME=/tmp/dagster-home
```

Lastly, we need to configure `dagster.yaml` to disable concurrency. Our example
is located at `/tmp/dagster-home/dagster.yaml`:

```yaml
run_queue:
  max_concurrent_runs: 1
```

This is currently a limitation with our `duckdb` integration. Please check out
[this issue](https://github.com/opensource-observer/oso/issues/2040#issue-2503231601)
for more information.

## Running Dagster

Now that we have everything set up, we can run the Dagster instance. Call this
command from the root of the repository:

```sh
uv run dagster dev
```

:::tip
Alternatively, you can use the `pnpm dev:dagster` command, which automates the setup process by creating the necessary directory and configuration file for you.
:::

:::tip
You may need to run the development server in legacy mode on resource-constrained machines.
See this [issue](https://github.com/opensource-observer/oso/issues/3366) for more details.

```bash
uv run dagster dev --use-legacy-code-server-behavior
```

:::

After a little bit of time, you should see the following message:

```sh
2024-09-10 22:35:31 +0200 - dagster.daemon - INFO - Instance is configured with the following daemons: ['AssetDaemon', 'BackfillDaemon', 'QueuedRunCoordinatorDaemon', 'SchedulerDaemon', 'SensorDaemon']
2024-09-10 22:35:31 +0200 - dagster-webserver - INFO - Serving dagster-webserver on http://127.0.0.1:3000 in process 1095
```

Head over to [http://localhost:3000](http://localhost:3000) to access Dagster's
UI. _Et voilà_! You have successfully set up Dagster locally.

## Define a new Dagster asset

Now you're ready to create a new Dagster software-defined asset.
You can use one of the following guides and come back to this guide to test it.

- 🗂️ [BigQuery Public Datasets](../bigquery.md) - Preferred and easiest route for sharing a dataset
- 🗄️ [Database Replication](../database.md) - Provide access to your database for replication as an OSO dataset
- 📈 [GraphQL API Crawler](../graphql-api.md) - Automatically crawl any GraphQL API
- 🌐 [REST API Crawler](../rest-api.md) - Automatically crawl any REST API
- 📁 [Files into Google Cloud Storage (GCS)](../gcs.md) - Drop Parquet/CSV files in our GCS bucket for loading into OSO
- ⚙️ [Custom Dagster Assets](../dagster.md) - Write a custom Dagster asset for unique data sources
- 📜 Static Files - Coordinate hand-off for high-quality data via static files. This path is predominantly used for [grant funding data](../funding-data.md).

## Test your asset locally

Assets in `warehouse/oso_dagster/assets/default` should automatically show up in
the Dagster assets list at `http://localhost:3000/assets`.

![Dagster assets](./dagster_assets.png)

Click on "Materialize" to start the job.
Here you'll be able to monitor the logs to debug any issues with
the data fetching.

:::warning
Unless your Dagster instance is configured with a Google account that has write
access to OSO BigQuery datasets, some dagster assets will fail to materialize.
Focus on debugging any issues with fetching data. When you're ready, work with a
core team member to test the asset in production.
:::

## Add your asset to production

### Submit a pull request

When you are ready to deploy,
submit a pull request of your changes to
[OSO](https://github.com/opensource-observer/oso).
OSO maintainers will work with you to get the code in shape for merging.
For more details on contributing to OSO, check out
[CONTRIBUTING.md](https://github.com/opensource-observer/oso/blob/main/CONTRIBUTING.md).

### Verify deployment

After your pull request is merged into the `main` branch, a new Dagster deployment is automatically triggered. This process typically takes 10-15 minutes.

You can monitor the deployment status and check the last update time for each code location in the [Deployment tab](https://dagster.opensource.observer/locations).

Once the deployment is complete, Dagster will automatically recognize your new asset, and it will appear in the [Global Asset List](https://dagster.opensource.observer/assets).

![Dagster assets](./dagster_assets.png)

If your asset is missing, you can check for loading errors
and the date of last code load in the
[Deployment tab](https://dagster.opensource.observer/locations).
For example, if your code has a bug and leads to a loading error,
it may look like this:

![Dagster deployment](./dagster_deployments.png)

### Run it!

If this is your first time adding an asset,
we suggest reaching out to the OSO team over
[Discord](https://www.opensource.observer/discord)
to run deploys manually.
You can monitor all Dagster runs
[here](https://dagster.opensource.observer/runs).

![Dagster run example](./dagster_run.png)

Dagster also provides
[automation](https://docs.dagster.io/concepts/automation)
to run jobs on a
[schedule](https://docs.dagster.io/concepts/automation/schedules)
(e.g. daily), after detecting a condition using a Python-defined
[sensor](https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors)
(e.g. when a file appears in GCS),
and using
[auto-materialization policies](https://docs.dagster.io/concepts/assets/asset-auto-execution).

We welcome any automation that can reduce the operational burden
in our continuous deployment.
However, before merging any job automation,
please reach out to the OSO devops team
on [Discord](https://www.opensource.observer/discord)
with an estimate of costs, especially if it involves large BigQuery scans.
We will reject or disable any jobs that lead to
increased infrastructure instability or unexpected costs.

## Advanced Topics

### Asset Code Locations

In order to improve the usability of our dagster setup locally, we've actually
split the organization of dagster assets into multiple "code locations." A code
location is a dagster abstraction that allows you to have different asset
definitions in entire different code paths. Code locations for an asset are
determined by the parent folder of the asset within
`warehouse/oso_dagster/assets` that corresponds to a definitions file in
`warehouse/oso_dagster/definitions/`. For _most_ new assets, they should be
added to `warehouse/oso_dagster/assets/default/`.

:::Note
At this time production is still using a _single_ code location. This is
due to an issue with how dagster handles scheduling and jobs. See [this
issue](https://github.com/opensource-observer/oso/issues/4840)
:::

#### Available Code Locations

At this moment, the available code locations can be found in the repository at
`warehouse/oso_dagster/definitions/`:

- `sqlmesh`: This is the code location for _any_ assets
  related to sqlmesh. This is essentially anything that depends on the
  `dagster-sqlmesh` package.
- `default`: The default code location for all remaining
  assets that do not fit into the other categories.

#### Running different code locations

To run these different code locations is nearly identical to how we run the
`default` code location. You just need to specify the code location's python
module path when running your Dagster jobs. To run the `sqlmesh` or `ops` code
location for example:

```bash
uv run dagster dev -m oso_dagster.definitions.sqlmesh
```

Notice that after `-m` the code location's module path is specified. It is
useful to note for newcomers that the `warehouse/` path in the repository is not
considered a python module as it does not contain a `__init__.py` file and does
not appear as a python module in the root `pyproject.toml`

### Running dagster with sqlmesh locally

This is mostly for the OSO team as most people should not need to run sqlmesh on
the dagster UI in a local fashion. It should be enough for anyone looking to add
models to run sqlmesh on it's own. The only reason to run sqlmesh locally is to
ensure that the dagster-sqlmesh integration is working as expected with our
particular pipeline.

Some environment variables need to be set in your `.env`:

```bash
# While not strictly necessary, you likely want the sqlmesh dagster asset
# caching enabled so restarting doesn't take so long.
DAGSTER_ASSET_CACHE_ENABLED=1
DAGSTER_ASSET_CACHE_DIR=/path/to/some/cache/dir # change this
# You can set this number to anything reasonable for your testing use case
DAGSTER_ASSET_CACHE_DEFAULT_TTL_SECONDS=3600
# `local` uses duckdb
# `local-trino` uses a locally deployed trino
# Suggestion is to use `local` as it's faster. This doc assumes duckdb.
DAGSTER_SQLMESH_GATEWAY=local
SQLMESH_TESTING_ENABLED=1
OSO_ENABLE_JSON_LOGS=0
```

Then you should run the sqlmesh local test setup to get your local sqlmesh
duckdb initialized with oso local seed data.

```bash
uv run oso local sqlmesh-test --duckdb
```

Now it should be possible run sqlmesh and dagster locally. When materializing
sqlmesh assets, it might complain about some out of date dependencies. Since we
ran the local test setup, the data it's depending on should have been added by
the oso local seed setup.

### Seed and Staging data

When creating new Dagster assets, it's important to also write a seed file before integrating it into a SQLMesh staging model.

The workflow is as follows:

1.  **Write the Asset**:
    - Follow the cursor rules for creating new assets.
    - Keep column names consistent with the original source.
    - Perform minimal normalization and unnesting.

2.  **Run Dagster Locally**:
    - Confirm that you can materialize the source correctly.

3.  **Submit and Merge a PR**:
    - Submit a pull request with your changes and merge it into production.

4.  **Materialize in Production**:
    - Materialize the asset in the production Dagster environment.

5.  **Verify Data**:
    - Sample the data in BigQuery to confirm it's correct.

6.  **Create Seed File and Staging Model**:
    - Follow the cursor rules for creating seed files and staging models.
    - Use a sample of 5-10 rows of real data from BigQuery that cover multiple cases.
    - If there are date fields, set them to `datetime.now()`.
    - Test locally with SQLMesh until there are no errors.

7.  **Submit and Merge a PR**:
    - Submit a pull request with the seed file and staging model and merge it into production.
