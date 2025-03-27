---
title: Dagster Guide
sidebar_position: 6
---

OSO uses Dagster to perform all data orchestration in our backend infrastructure.
Most of the time, contributors will be working in Dagster to
connect new data sources.
If the source data already exists in OSO, take a look at
[contributing models via sqlmesh](../contribute-models/index.mdx).

In order to setup Dagster in your development environment,
check out the [getting started guide](../contribute-data/setup/index.md).

## Data Architecture

As much as possible, we store data in an Iceberg cluster,
making it the center of gravity of the OSO data lake.
Thus, data ingest will typically go into Iceberg tables.
[`pyoso`](../get-started/python.md) is the best way to query any data in these tables.
This will make it significantly easier to decentralize OSO infrastructure
in the future.

## Job schedules

All automated job schedules can be found on our public
[Dagster dashboard](https://dagster.opensource.observer/automation).

Currently, our main data pipeline runs once per week on Sundays.

## Alert system

Dagster alert sensors are configured in
[`warehouse/oso_dagster/factories/alerts.py`](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/factories/alerts.py)

Right now, alerts are reported to `#alerts` in the
[OSO Discord server](https://www.opensource.observer/discord).

## Secrets Management

### Local secrets manager

### Production secrets
