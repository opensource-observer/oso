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

---

The following diagram illustrates Open Source Observer's technical architecture.

[![OSO Architecture Diagram](https://mermaid.ink/img/pako:eNqNVMtu2zAQ_BWCJxuI0rsPAfLorU4cuO3F7GFFbS0iEinwYcUN8u9dSpQly00RHiRqNcNZzi72jUtTIF_xLMuE9spXuGKCPzWo2dYEK5E95Q7tAS27tbJUHqUPFgUXuqMI_bsyrSzBevb9TmhGy4V8b6EpWRPySsmd4LfSG-vY4tHoDF9LCM6rAy4F_9Uz4gok4wj7I77P_hR4iD8ewAP7qvdK4xwBGqqj8yfUViqk21DkBENd9JtOh2UZXfOnwpZ9Yc8B7VFwit0w40yLeY-Muj1whoBGzRH3Rnur8uCRRUcTVukCX9H24CHJC8L2-VvCS1M3FMnBy3Lm5QsQGnb_rk13y9GOsQCqwYr8ItoalGadOZsUPHMwrpTtYKI0VYWpcPeVCUXnwvKC1oLF0pCtu0ViniJscaf2A205400vu0ses8Yaic51okXuz9VONYxr3KW8L3wtKJdk7CmjkdVXmoTbtr02ZKrrPL02U0_Pwf9vhoSjbzqUnp85lGCXh8a8c5jmOkQGh-OeLTbG-b1Fap-Zu-Nu6nEvtAaPVkGl_uCHcp9hTRwdiWPhO9amL-aHzU315Fe8RluDKmgIvcWw4L7EmmTiICrAvsRZ8044CN5sj1rylbcBr3hoKHN8UEC9Xg9BLBR17Lofat1se_8LDu-M4g?type=png)](https://mermaid.live/edit#pako:eNqNVMtu2zAQ_BWCJxuI0rsPAfLorU4cuO3F7GFFbS0iEinwYcUN8u9dSpQly00RHiRqNcNZzi72jUtTIF_xLMuE9spXuGKCPzWo2dYEK5E95Q7tAS27tbJUHqUPFgUXuqMI_bsyrSzBevb9TmhGy4V8b6EpWRPySsmd4LfSG-vY4tHoDF9LCM6rAy4F_9Uz4gok4wj7I77P_hR4iD8ewAP7qvdK4xwBGqqj8yfUViqk21DkBENd9JtOh2UZXfOnwpZ9Yc8B7VFwit0w40yLeY-Muj1whoBGzRH3Rnur8uCRRUcTVukCX9H24CHJC8L2-VvCS1M3FMnBy3Lm5QsQGnb_rk13y9GOsQCqwYr8ItoalGadOZsUPHMwrpTtYKI0VYWpcPeVCUXnwvKC1oLF0pCtu0ViniJscaf2A205400vu0ses8Yaic51okXuz9VONYxr3KW8L3wtKJdk7CmjkdVXmoTbtr02ZKrrPL02U0_Pwf9vhoSjbzqUnp85lGCXh8a8c5jmOkQGh-OeLTbG-b1Fap-Zu-Nu6nEvtAaPVkGl_uCHcp9hTRwdiWPhO9amL-aHzU315Fe8RluDKmgIvcWw4L7EmmTiICrAvsRZ8044CN5sj1rylbcBr3hoKHN8UEC9Xg9BLBR17Lofat1se_8LDu-M4g)

## Major Components

---

The architecture has the following major components.

### Data Warehouse

A major dependency of the system is BigQuery. BigQuery is the main storage of the public data warehouse that OSO enables. All of the collected data or aggregated views used by OSO is also made publicly available here (if it is not already a public dataset on BigQuery). External integrators can opt to use this data as they wish.

### Data Collectors

Data collection for the data warehouse is handled by plugins that are
currently executed based on a set schedule or some event in the data
pipelines. In the future, we will allow execution to occur in a more event
driven manner. This would reduce any computing overhead required.

### Query Processors

Query processors are either single SQL queries or an entire data pipeline
run against data in the data warehouse that is then materialized and
stored for later querying.

### API

The API can be used by external developers to integrate insights from OSO.
Rate limits or cost sharing subscriptions may apply to it's usage depending
on the systems used. This also powers the OSO website.

### Website

This is the OSO website at [https://www.opensource.observer](https://www.opensource.observer). This website provides an easy to use public view into the data.

## Dependent Technologies

---

Our infrastructure is based on many wonderful existing tools. Our major
dependencies are:

- Google BigQuery
  - As explained above, all of the data that OSO collects and materializes lives
    in public datasets in bigquery.
- dbt
  - This is used for data transformations to turn collected data into useful
    materializations for the OSO website.
- CloudQuery
  - CloudQuery enables the collection of data from external sources as well as
    handling the flow of data through the main data pipeline. Any data from and to
    or inside and outside the "Main Data Pipeline" is managed by cloudquery. All of our
    data collectors are written as [CloudQuery](https://docs.airbyte.com/)
    plugins.
- PostgreSQL
  - Used mostly as a host of the materialized views from the Query Processors
    that is used to power the OSO website. This is used to offload querying of
    the most used views from bigquery as using bigquery to serve the OSO website
    would become cost prohibitive.

## Indexing Pipeline

---

OSO maintains an [ETL](https://en.wikipedia.org/wiki/Extract%2C_load%2C_transform) data pipeline that is continuously deployed from our [monorepo](https://github.com/opensource-observer/oso/) and regularly indexes all available event data about projects in the [oss-directory](https://github.com/opensource-observer/oss-directory).

- **Extract**: raw event data from a variety of public data sources (e.g., GitHub, blockchains, npm, Open Collective)
- **Transform**: the raw data into impact metrics and impact vectors per project (e.g., # of active developers)
- **Load**: the results into various OSO data products (e.g., our API, website, widgets)

## Open Architecture for Open Source Data

The architecture is designed to accomodate a collaborative data pipeline that
can be used to formulate a better understanding of projects' impact across various dimensions.
The data collected and the code used to build the system are all built in the open with a
goal of transparency for costs and development. As illustrated in the
architectural diagram, the main data pipeline feeds into a database
that is used to enable the OSO website, but the materialized data within the data
warehouse of that pipeline can be used by any external system as well.

The main units of contribution are described as the actions available
to **Impact Data Scientists** and **Data Engineers**. Data Engineers can easily contribute
by building more CloudQuery plugins for data collection. Impact Data Scientists can
help by contributing additional data transformations to the query processors.
With the infrastructure automation in the OSO repository, either contribution
will be automatically deployed once merged into the `main` branch. If for
whatever reason none of these options fit an engineer or analyst's needs, there
is also the option to extract data from the platform entirely. This option will
likely incur additional costs for the individual on their GCP account.
