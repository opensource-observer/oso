---
title: Contributors Overview
---

# Contributors Welcome!

We believe that the only way we can surface the best data for the Open Source
Community is to build tools and collect data in the open. However, before
starting any contribution to OSO, it is important to understand the general
architecture.

## Architectural Overview

_(TODO Architectural Diagram)_

_As part of our dedication to our promise of Open Infrastructure, all of the
code for this architecture is available to view/copy/redeploy [in our
monorepo](https://github.com/opensource-observer/oso)._

### Summary

The architecture has the following major components

- Website
  - This is the OSO website at
    [https://opensource.observer](https://opensource.observer). This website
    provides an easy to use public view into the data.
- API
  - The API can be used by external developers to integrate insights from OSO.
    Rate limits or cost sharing subscriptions may apply to it's usage depending
    on the systems used. This also powers the OSO website.
- OSO Data Warehouse
  - A major dependency of the system is BigQuery. BigQuery is the main storage
    of the public data warehouse that OSO enables. All of the collected data or
    aggregated views used by OSO is also made publicly available here (if it is
    not already a public dataset on BigQuery). External integrators can opt to
    use this data as they wish.
- Query Processors
  - Query processors are either single SQL queries or an entire data pipeline
    run against data in the data warehouse that is then materialized and
    stored for later querying.
- Data Oracles
  - TBD

### Dependent Technologies

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
