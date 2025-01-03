---
title: Technical Architecture
sidebar_position: 1
---

:::info
OSO's goal is to make it simple to contribute by providing an automatically
deployed data pipeline so that the community can build this open data warehouse
together. All of the code for this architecture is available to view/copy/redeploy from the [OSO Monorepo](https://github.com/opensource-observer/oso).
:::

## Pipeline Overview

OSO maintains an [ETL](https://en.wikipedia.org/wiki/Extract%2C_load%2C_transform) data pipeline that is continuously deployed from our [monorepo](https://github.com/opensource-observer/oso/) and regularly indexes all available event data about projects in the [oss-directory](https://github.com/opensource-observer/oss-directory).

- **Extract**: raw event data from a variety of public data sources (e.g., GitHub, blockchains, npm, Open Collective)
- **Transform**: the raw data into impact metrics and impact vectors per project (e.g., # of active developers)
- **Load**: the results into various OSO data products (e.g., our API, website, widgets)

The following diagram illustrates Open Source Observer's technical architecture.
[![OSO Architecture](https://mermaid.ink/img/pako:eNqVVU1z2jAQ_SsancwktNMcOXSGhHbaTgikNOkB9yDLC1ZjS44-gDST_96VLXDAhja-gFfvzdt9u149U65SoAPa7_djaYXNYUBiOilBkplymgOZJAb0CjQZap4JC9w6DTGNZUWJ5SJXa54xbcmPy1gSfIxLlpqVGSldkgs-j-mQW6UNiW6U7MMmY85YsYJeTH_VDP84lDGIvfO_eycprPzBiFlGPsmlkHCIYJLlT8buUDMuAKvByA4GMq3_VDqk38cy7wWsyXty60A_xRRjH4kyag1JjfS6NfAAwUpxiLhS0mqROAvEOxqwQqawAV2Dt0m2CLPb64DnqigxkjDLsy7SdyfJI-YiwATGmmnIFNZUww8agLnOu7tZ-dIY2LRMlJCjwx-QN2ZCksrPaYjume4fhTMBxmpmhZKe800l-0ESjdjSWNC9Fjm4s20aV3kOYVDS3Lbxu1rnUaDsIiS6FMuqS0jrHfBeuzoPzSSlVhyMqdUSezS7VrdSFO42v0uvpo8ZGiBYLv7AaWpTUMWb1kkenY7dYDev_yPuS0iY1z4xARdo1WeNdaPAW6bg4o1TsE3GN3VyPZxWWj5AoivcHg-VHR1dNY95Aaa7oeHsuFiXvYHUqfJvJ4-0o94W7S1ysgWLYPvrDvjPVnAwbfOrjYXQn5AQVpboWbD8HvCLz89uYGPf_Ta9Libm5tfz9CsJSz76wozT7GxY4teoekfUTm_FvXXbbKXmHx7Sc1qALphI8fJ59uGY2gwKNNZfQCnTD_6OeUEcc1bNniSnA6sdnFOt3DKjgwXLDb65Eq2EkWBoXbGFQCpwj4zrq6264V7-AjpFJyI?type=png)](https://mermaid.live/edit#pako:eNqVVU1z2jAQ_SsancwktNMcOXSGhHbaTgikNOkB9yDLC1ZjS44-gDST_96VLXDAhja-gFfvzdt9u149U65SoAPa7_djaYXNYUBiOilBkplymgOZJAb0CjQZap4JC9w6DTGNZUWJ5SJXa54xbcmPy1gSfIxLlpqVGSldkgs-j-mQW6UNiW6U7MMmY85YsYJeTH_VDP84lDGIvfO_eycprPzBiFlGPsmlkHCIYJLlT8buUDMuAKvByA4GMq3_VDqk38cy7wWsyXty60A_xRRjH4kyag1JjfS6NfAAwUpxiLhS0mqROAvEOxqwQqawAV2Dt0m2CLPb64DnqigxkjDLsy7SdyfJI-YiwATGmmnIFNZUww8agLnOu7tZ-dIY2LRMlJCjwx-QN2ZCksrPaYjume4fhTMBxmpmhZKe800l-0ESjdjSWNC9Fjm4s20aV3kOYVDS3Lbxu1rnUaDsIiS6FMuqS0jrHfBeuzoPzSSlVhyMqdUSezS7VrdSFO42v0uvpo8ZGiBYLv7AaWpTUMWb1kkenY7dYDev_yPuS0iY1z4xARdo1WeNdaPAW6bg4o1TsE3GN3VyPZxWWj5AoivcHg-VHR1dNY95Aaa7oeHsuFiXvYHUqfJvJ4-0o94W7S1ysgWLYPvrDvjPVnAwbfOrjYXQn5AQVpboWbD8HvCLz89uYGPf_Ta9Libm5tfz9CsJSz76wozT7GxY4teoekfUTm_FvXXbbKXmHx7Sc1qALphI8fJ59uGY2gwKNNZfQCnTD_6OeUEcc1bNniSnA6sdnFOt3DKjgwXLDb65Eq2EkWBoXbGFQCpwj4zrq6264V7-AjpFJyI)

## Major Components

The architecture has the following major components.

### Data Orchestration

Dagster is the central data orchestration system, which manages the entire pipeline,
from the data ingestion (e.g. via [dlt](https://docs.dagster.io/integrations/embedded-elt/dlt) connectors), the [dbt](https://docs.dagster.io/integrations/dbt) pipeline, the [sqlmesh](https://github.com/opensource-observer/dagster-sqlmesh) pipeline, to copying mart models to data serving infrastructure.

You can see our public Dagster dashboard at
[https://dagster.opensource.observer/](https://dagster.opensource.observer/).

### Data Warehouse

Currently all data is stored and processed in
[Google BigQuery](https://cloud.google.com/bigquery/?hl=en).
All of the collected data or aggregated views used by OSO is also made publicly available here (if it is not already a public dataset on BigQuery).
Anyone with can view, query, or build off of any stage in the pipeline.
In the future we plan to explore a decentralized lakehouse.

To see all datasets that you can subscribe to, check out our
[Data Overview](../integrate/datasets/index.mdx).

### dbt pipeline

We use a [dbt](https://www.getdbt.com/) pipeline to clean and normalize the data
into a universal event table. You can read more about our event model
[here](./event.md).

### OLAP database

We use [Clickhouse](https://clickhouse.com/)
as a frontend database for serving live queries to the API server
and frontend website, as well as running a sqlmesh data pipeline.

### sqlmesh pipeline

A [sqlmesh](https://sqlmesh.com/) pipeline
is used for computing time series metrics from
the universal event table, which is copied from the BigQuery dbt pipeline.

### API service

We use [Hasura](https://hasura.io/) to automatically generate
a GraphQL API from our Clickhouse database.
We then use an [Apollo Router](https://www.apollographql.com/docs/router/)
to service user queries to the public.
The API can be used by external developers to integrate insights from OSO.
Rate limits or cost sharing subscriptions may apply to its usage depending
on the systems used. This also powers the OSO website.

### OSO Website

The OSO website is served at
[https://www.opensource.observer](https://www.opensource.observer).
This website provides an easy to use public view into the data.
We currently use [Next.js](https://nextjs.org/)
hosted by [Vercel](https://vercel.com/).

## Open Architecture for Open Source Data

The architecture is designed to be fully open to maximum open source collaboration.
With contributions and guidance from the community,
we want Open Source Observer to evolve as we better understand
what impact looks like in different domains.

All code is open source in our
[monorepo](https://github.com/opensource-observer/oso).
All data, including every stage in our pipeline, is publicly available on
[BigQuery](https://console.cloud.google.com/bigquery/analytics-hub/exchanges/projects/87806073973/locations/us/dataExchanges/open_source_observer_190181416ae).
All data orchestration is visible in our public
[Dagster dashboard](https://dagster.opensource.observer/).

You can read more about our open philosophy on our
[blog](https://kariba.substack.com/p/open-source-open-data-open-infra).
