---
title: Getting Started with Dagster
sidebar_position: 0
---

[Dagster](https://dagster.io) is a data orchestrator that allows you to define
data pipelines in a declarative way. It is a powerful tool that allows you to
define the flow of data from source to destination, and to define the
transformations that data undergoes along the way.

At OSO, we use Dagster to process data from
[various sources](https://github.com/opensource-observer/oso/tree/main/warehouse/oso_dagster/assets),
transform it, and load it into BigQuery. This quickstart guide will help you set
up our Dagster instance locally, with a [`duckdb`](http://duckdb.org/) backend,
in order to follow along with our tutorials in the next sections.

## Check pipeline status

[https://dagster.opensource.observer](https://dagster.opensource.observer)

Use this to view the entire data infrastructure,
as well as the current status of every stage of the pipeline.

Admins can trigger runs
[here](https://admin-dagster.opensource.observer/)

## Setting up Dagster

First, we need to clone the
[OSO GitHub repository](http://github.com/opensource-observer/oso) and install
the required dependencies.

```sh
git clone git@github.com:opensource-observer/oso.git .
```

Install the dependencies with
[uv](https://docs.astral.sh/uv/):

```sh
uv sync
```

Now, let's fill the `.env` file with the required environment variables:

```sh
GOOGLE_PROJECT_ID=<your-google-project-id>
DAGSTER_DBT_PARSE_PROJECT_ON_LOAD=1
DAGSTER_HOME=/tmp/dagster-home
```

After setting the environment variables, Dagster needs `$DAGSTER_HOME` to be
created before running the Dagster instance.

```sh
mkdir /tmp/dagster-home
```

:::info

Lastly, we need to configure `dagster.yaml` to disable concurrency. Our example
is located at `/tmp/dagster-home/dagster.yaml`:

This is currently a limitation with our `duckdb` integration. Please check out
[this issue](https://github.com/opensource-observer/oso/issues/2040#issue-2503231601)
for more information.

```yaml
run_queue:
  max_concurrent_runs: 1
```

:::

## Running Dagster

Now that we have everything set up, we can run the Dagster instance:

```sh
uv run dagster dev
```

After a little bit of time, you should see the following message:

```sh
2024-09-10 22:35:31 +0200 - dagster.daemon - INFO - Instance is configured with the following daemons: ['AssetDaemon', 'BackfillDaemon', 'QueuedRunCoordinatorDaemon', 'SchedulerDaemon', 'SensorDaemon']
2024-09-10 22:35:31 +0200 - dagster-webserver - INFO - Serving dagster-webserver on http://127.0.0.1:3000 in process 1095
```

Head over to [http://localhost:3000](http://localhost:3000) to access Dagster's
UI. _Et voilà_! You have successfully set up Dagster locally.

This is just the beginning. Check out how to create a
[DLT Dagster Asset](../../contribute-data/api-crawling/index.md) next and start building!
