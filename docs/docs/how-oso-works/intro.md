---
title: Overview
sidebar_position: 1
---

:::warning
This page is a work in progress.
:::

We believe that the only way we can surface the best data for the open source
community is to build tools and collect data in the open. However, before
starting any contribution to OSO, it is important to understand some of the
building blocks and general architecture of our dataset.

## Building Blocks

We have four primary building blocks that we use to organize our data:

- [Collections](./schema/collection). Collections are used to group projects
  together. For example, a collection may include all projects that are part of
  a particular ecosystem or all projects that are dependent on a given developer
  library.
- [Projects](./schema/project). Projects are used to group artifacts together.
  For example, a project like Open Source Observer may include a GitHub organization,
  various NPM packages, an API endpoint,
  an Open Collective for raising funds for the project,
  and a blockchain address used for holding crypto funds.
- [Artifacts](./schema/artifact). Artifacts are used to store information about
  work artifacts created by open source projects in the OSS Directory. For
  example, a GitHub organization artifact would be identified by a `url` field
  that is a valid GitHub organization URL (eg,
  `https://github.com/opensource-observer`) and a blockchain address artifact
  would be identified by an `address` field that is a valid blockchain address
  (eg, `0x1234567890123456789012345678901234567890`).
- [Events](./schema/events). Events are used to store information about transactions or
  other activities involving artifacts. These could include a code
  commit, a package download, or a smart contract interaction.

It is easy to define new collections, projects, and artifacts in our [OSS
Directory](https://github.com/opensource-oberver/oss-directory). Once these
exist, we will automatically start collecting event data for them.

## Architecture

### Diagram

> As part of our dedication to our promise of Open Infrastructure, all of the
> code for this architecture is available to view/copy/redeploy [in our
> monorepo](https://github.com/opensource-observer/oso).

[![OSO Architecture Diagram](https://mermaid.ink/img/pako:eNqNVMtu2zAQ_BWCJxuI0rsPAfLorU4cuO3F7GFFbS0iEinwYcUN8u9dSpQly00RHiRqNcNZzi72jUtTIF_xLMuE9spXuGKCPzWo2dYEK5E95Q7tAS27tbJUHqUPFgUXuqMI_bsyrSzBevb9TmhGy4V8b6EpWRPySsmd4LfSG-vY4tHoDF9LCM6rAy4F_9Uz4gok4wj7I77P_hR4iD8ewAP7qvdK4xwBGqqj8yfUViqk21DkBENd9JtOh2UZXfOnwpZ9Yc8B7VFwit0w40yLeY-Muj1whoBGzRH3Rnur8uCRRUcTVukCX9H24CHJC8L2-VvCS1M3FMnBy3Lm5QsQGnb_rk13y9GOsQCqwYr8ItoalGadOZsUPHMwrpTtYKI0VYWpcPeVCUXnwvKC1oLF0pCtu0ViniJscaf2A205400vu0ses8Yaic51okXuz9VONYxr3KW8L3wtKJdk7CmjkdVXmoTbtr02ZKrrPL02U0_Pwf9vhoSjbzqUnp85lGCXh8a8c5jmOkQGh-OeLTbG-b1Fap-Zu-Nu6nEvtAaPVkGl_uCHcp9hTRwdiWPhO9amL-aHzU315Fe8RluDKmgIvcWw4L7EmmTiICrAvsRZ8044CN5sj1rylbcBr3hoKHN8UEC9Xg9BLBR17Lofat1se_8LDu-M4g?type=png)](https://mermaid.live/edit#pako:eNqNVMtu2zAQ_BWCJxuI0rsPAfLorU4cuO3F7GFFbS0iEinwYcUN8u9dSpQly00RHiRqNcNZzi72jUtTIF_xLMuE9spXuGKCPzWo2dYEK5E95Q7tAS27tbJUHqUPFgUXuqMI_bsyrSzBevb9TmhGy4V8b6EpWRPySsmd4LfSG-vY4tHoDF9LCM6rAy4F_9Uz4gok4wj7I77P_hR4iD8ewAP7qvdK4xwBGqqj8yfUViqk21DkBENd9JtOh2UZXfOnwpZ9Yc8B7VFwit0w40yLeY-Muj1whoBGzRH3Rnur8uCRRUcTVukCX9H24CHJC8L2-VvCS1M3FMnBy3Lm5QsQGnb_rk13y9GOsQCqwYr8ItoalGadOZsUPHMwrpTtYKI0VYWpcPeVCUXnwvKC1oLF0pCtu0ViniJscaf2A205400vu0ses8Yaic51okXuz9VONYxr3KW8L3wtKJdk7CmjkdVXmoTbtr02ZKrrPL02U0_Pwf9vhoSjbzqUnp85lGCXh8a8c5jmOkQGh-OeLTbG-b1Fap-Zu-Nu6nEvtAaPVkGl_uCHcp9hTRwdiWPhO9amL-aHzU315Fe8RluDKmgIvcWw4L7EmmTiICrAvsRZ8044CN5sj1rylbcBr3hoKHN8UEC9Xg9BLBR17Lofat1se_8LDu-M4g)

### Major Components

The architecture has the following major components

- [Data Warehouse](./architecture/warehouse)
  - A major dependency of the system is BigQuery. BigQuery is the main storage
    of the public data warehouse that OSO enables. All of the collected data or
    aggregated views used by OSO is also made publicly available here (if it is
    not already a public dataset on BigQuery). External integrators can opt to
    use this data as they wish.
- [Data Collectors](./architecture/data-collection)
  - Data collection for the data warehouse is handled by plugins that are
    currently executed based on a set schedule or some event in the data
    pipelines. In the future, we will allow execution to occur in a more event
    driven manner. This would reduce any computing overhead required.
- [Query Processors](./architecture/query-processors)
  - Query processors are either single SQL queries or an entire data pipeline
    run against data in the data warehouse that is then materialized and
    stored for later querying.
- [API](../integrate/getting-started)
  - The API can be used by external developers to integrate insights from OSO.
    Rate limits or cost sharing subscriptions may apply to it's usage depending
    on the systems used. This also powers the OSO website.
- Website
  - This is the OSO website at
    [https://www.opensource.observer](https://www.opensource.observer). This website
    provides an easy to use public view into the data.

### Dependent Technologies

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
- [Hasura](https://hasura.io/)
  - Hasura is used to provide a GraphQL API to the PostgreSQL database.
    The API service is meant for powering live applications,
    including the OSO website.
- [Supabase](https://supabase.com/)
  - We maintain a separate database via Supabase.
    Supabase is used for user authentication, as well as storing sensitive user data.
    While nearly every other part of the architecture will be
    transparent and publicly readable, this database will be kept private.

## Open Architecture for Open Source Data

The architecture is designed to accomodate a collaborative data pipeline that
can be used to formulate a better understanding of a project's impact. The data
collected and the code used to build the system are all built in the open with a
goal of transparency for costs and development. As illustrated in the
architectural diagram, the Main Data Pipeline feeds into a PostgreSQL database
that is used to enable the OSO website, but the materialized data within the data
warehouse of that pipeline can be used by any external system as well.

Our goal is to make it simple to contribute by providing an automatically
deployed data pipeline so that the community can build this open data warehouse
together. The main units of contribution are described as the actions available
to `Data Scientists` and `Data Engineers`. Data Engineers can easily contribute
by building more cloudquery plugins for data collection. Data Scientists can
help by contributing additional data transformations to the query processors.
With the infrastructure automation in the OSO repository, either contribution
will be automatically deployed once merged into the `main` branch. If for
whatever reason none of these options fit an engineer's/analyst's needs, there
is also the option to extract data from the platform entirely. This option will
likely incur additional costs for the individual on their GCP account.
