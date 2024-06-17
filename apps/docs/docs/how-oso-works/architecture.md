---
title: Technical Architecture
sidebar_position: 5
---

:::info
OSO's goal is to make it simple to contribute by providing an automatically
deployed data pipeline so that the community can build this open data warehouse
together. All of the code for this architecture is available to view/copy/redeploy from the [OSO Monorepo](https://github.com/opensource-observer/oso).
:::

## Diagram

The following diagram illustrates Open Source Observer's technical architecture.

[![OSO Architecture Diagram](https://mermaid.ink/img/pako:eNqNVMtu2zAQ_BWCJxuI0rsPAfLorU4cuO3F7GFFbS0iEinwYcUN8u9dSpQly00RHiRqNcNZzi72jUtTIF_xLMuE9spXuGKCPzWo2dYEK5E95Q7tAS27tbJUHqUPFgUXuqMI_bsyrSzBevb9TmhGy4V8b6EpWRPySsmd4LfSG-vY4tHoDF9LCM6rAy4F_9Uz4gok4wj7I77P_hR4iD8ewAP7qvdK4xwBGqqj8yfUViqk21DkBENd9JtOh2UZXfOnwpZ9Yc8B7VFwit0w40yLeY-Muj1whoBGzRH3Rnur8uCRRUcTVukCX9H24CHJC8L2-VvCS1M3FMnBy3Lm5QsQGnb_rk13y9GOsQCqwYr8ItoalGadOZsUPHMwrpTtYKI0VYWpcPeVCUXnwvKC1oLF0pCtu0ViniJscaf2A205400vu0ses8Yaic51okXuz9VONYxr3KW8L3wtKJdk7CmjkdVXmoTbtr02ZKrrPL02U0_Pwf9vhoSjbzqUnp85lGCXh8a8c5jmOkQGh-OeLTbG-b1Fap-Zu-Nu6nEvtAaPVkGl_uCHcp9hTRwdiWPhO9amL-aHzU315Fe8RluDKmgIvcWw4L7EmmTiICrAvsRZ8044CN5sj1rylbcBr3hoKHN8UEC9Xg9BLBR17Lofat1se_8LDu-M4g?type=png)](https://mermaid.live/edit#pako:eNqNVMtu2zAQ_BWCJxuI0rsPAfLorU4cuO3F7GFFbS0iEinwYcUN8u9dSpQly00RHiRqNcNZzi72jUtTIF_xLMuE9spXuGKCPzWo2dYEK5E95Q7tAS27tbJUHqUPFgUXuqMI_bsyrSzBevb9TmhGy4V8b6EpWRPySsmd4LfSG-vY4tHoDF9LCM6rAy4F_9Uz4gok4wj7I77P_hR4iD8ewAP7qvdK4xwBGqqj8yfUViqk21DkBENd9JtOh2UZXfOnwpZ9Yc8B7VFwit0w40yLeY-Muj1whoBGzRH3Rnur8uCRRUcTVukCX9H24CHJC8L2-VvCS1M3FMnBy3Lm5QsQGnb_rk13y9GOsQCqwYr8ItoalGadOZsUPHMwrpTtYKI0VYWpcPeVCUXnwvKC1oLF0pCtu0ViniJscaf2A205400vu0ses8Yaic51okXuz9VONYxr3KW8L3wtKJdk7CmjkdVXmoTbtr02ZKrrPL02U0_Pwf9vhoSjbzqUnp85lGCXh8a8c5jmOkQGh-OeLTbG-b1Fap-Zu-Nu6nEvtAaPVkGl_uCHcp9hTRwdiWPhO9amL-aHzU315Fe8RluDKmgIvcWw4L7EmmTiICrAvsRZ8044CN5sj1rylbcBr3hoKHN8UEC9Xg9BLBR17Lofat1se_8LDu-M4g)

## Major Components

The architecture has the following major components.

### Data Warehouse

Currently all data is stored and processed in Google BigQuery.
All of the collected data or aggregated views used by OSO is also made publicly available here (if it is not already a public dataset on BigQuery).
Anyone with can view, query, or build off of any stage in the pipeline.
In the future we plan to explore a decentralized lakehouse.

### Data Orchestration

Dagster is the central orchestration system, which manages the entire pipeline,
from the data ingestion, the dbt pipeline, to copying marts to data serving infrastructure.

### API

The API can be used by external developers to integrate insights from OSO.
Rate limits or cost sharing subscriptions may apply to it's usage depending
on the systems used. This also powers the OSO website.

### Website

This is the OSO website at [https://www.opensource.observer](https://www.opensource.observer). This website provides an easy to use public view into the data.

## Dependent Technologies

Our infrastructure is based on many wonderful existing tools. Our major
dependencies are:

- Google BigQuery
  - As explained above, all of the data that OSO collects and materializes lives
    in public datasets in BigQuery.
- Dagster
  - Dagster orchestrates all data jobs, including the collection of data
    from external sources as well as handling the flow of data through the
    main data pipeline.
- dbt
  - This is used for data transformations to turn collected data into useful
    materializations for the OSO API and website.
- OLAP database
  - All dbt mart models are copied to an OLAP database for real-time queries.
    This database powers the OSO API, which in turn powers the OSO website.

## Indexing Pipeline

OSO maintains an [ETL](https://en.wikipedia.org/wiki/Extract%2C_load%2C_transform) data pipeline that is continuously deployed from our [monorepo](https://github.com/opensource-observer/oso/) and regularly indexes all available event data about projects in the [oss-directory](https://github.com/opensource-observer/oss-directory).

- **Extract**: raw event data from a variety of public data sources (e.g., GitHub, blockchains, npm, Open Collective)
- **Transform**: the raw data into impact metrics and impact vectors per project (e.g., # of active developers)
- **Load**: the results into various OSO data products (e.g., our API, website, widgets)

## Open Architecture for Open Source Data

The architecture is designed to fully open to open source collaboration.
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
