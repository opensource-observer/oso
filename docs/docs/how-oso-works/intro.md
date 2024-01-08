---
title: Overview
sidebar_position: 1
---

:::warning
This page is a work in progress.
:::

We believe that the only way we can surface the best data for the open source
community is to build tools and collect data in the open. However, before
starting any contribution to OSO, it is important to understand some of the building blocks and general
architecture of our dataset.

## Building Blocks

We have four primary building blocks that we use to organize our data:

- [Collections](./collection-schema). Collections are used to group projects
  together. For example, a collection may include all projects that are part of
  a particular ecosystem or all projects that are dependent on a given developer
  library.
- [Projects](./project-schema). Projects are used to group artifacts together.
  For example, a project may include a GitHub organization, a blockchain
  address used for holding funds, and a NPM package.
- [Artifacts](./artifact-schemas). Artifacts are used to store information about
  work artifacts created by open source projects in the OSS Directory. For
  example, a GitHub organization artifact would be identified by a `url` field
  that is a valid GitHub organization URL (eg, `https://github.com/opensource-observer`)
  and a blockchain address artifact would be identified by an `address` field that is
  a valid blockchain address (eg, `0x1234567890123456789012345678901234567890`).
- [Events](./events). Events are used to store information about transactions or other
  activities involving a project's artifacts. These could include a code commit,
  a package download, or a smart contract interaction.

It is easy to define new collections, projects, and artifacts in our
[OSS Directory](https://github.com/opensource-oberver/oss-directory). Once these exist,
we will automatically start collecting event data for them.

## General Architecture

> As part of our dedication to our promise of Open Infrastructure, all of the
> code for this architecture is available to view/copy/redeploy [in our
> monorepo](https://github.com/opensource-observer/oso).

_(TODO Architectural Diagram)_

## Major Components

The architecture has the following major components

- [Data Warehouse](./warehouse)
  - A major dependency of the system is BigQuery. BigQuery is the main storage
    of the public data warehouse that OSO enables. All of the collected data or
    aggregated views used by OSO is also made publicly available here (if it is
    not already a public dataset on BigQuery). External integrators can opt to
    use this data as they wish.
- [Connectors](./connectors)
  - aka Data Oracles
- [Query Processors](./query-processors)
  - Query processors are either single SQL queries or an entire data pipeline
    run against data in the data warehouse that is then materialized and
    stored for later querying.
- [API](../api/intro)
  - The API can be used by external developers to integrate insights from OSO.
    Rate limits or cost sharing subscriptions may apply to it's usage depending
    on the systems used. This also powers the OSO website.
- Website
  - This is the OSO website at
    [https://www.opensource.observer](https://www.opensource.observer). This website
    provides an easy to use public view into the data.

## Dependent Technologies

Our infrastructure is based on many wonderful existing tools. Our major
dependencies are:

- Google BigQuery
  - As explained above, all of the data that OSO collects and materializes lives
    in public datasets in bigquery.
- dbt
  - This is used for data transformations to turn collected data into useful
    materializations for the OSO website.
- airbyte
  - Moves data from and to or inside and outside the OSO platform. All of our
    data collectors are written as [airbyte](https://docs.airbyte.com/)
    connectors and published to the [airbyte connector
    registry](https://connectors.airbyte.com/files/generated_reports/connector_registry_report.html).
    In general, data movement outside of the OSO website and API are handled by
    airbyte.
- dagster
  - Combines dbt transformations and airbyte connectors into pipelines that make
    up all transformations from the original data source to the either the data
    oracles or the database used to power the OSO website.
- PostgreSQL
  - Used mostly as a host of the materialized views from the Query Processors
    that is used to power the OSO website.
