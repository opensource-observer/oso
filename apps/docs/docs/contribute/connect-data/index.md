---
title: Connect Your Data
sidebar_position: 0
---

:::info
We're always looking for new data sources to integrate with OSO and deepen our community's understanding of open source impact. If you're a developer or data engineer, please reach out to us on [Discord](https://www.opensource.observer/discord). We'd love to partner with you to connect your database (or other external data sources) to the OSO data warehouse.
:::

There are currently the following patterns for integrating new data sources into OSO,
in order of preference:

1. [**BigQuery public datasets**](./bigquery/index.md): If you can maintain a BigQuery public dataset, this is the preferred and easiest route.
2. [**Database replication**](./database.md): Replicate your database into an OSO dataset (e.g. from Postgres).
3. [**API crawling**](./api.md): Crawl an API by writing a plugin.
4. [**Files into Google Cloud Storage (GCS)**](./gcs.md): You can drop Parquet/CSV files in our GCS bucket for loading into BigQuery.
5. [**Custom Dagster assets**](./dagster.md): Write a custom Dagster asset for other unique data sources.
6. **Static files**: If the data is high quality and can only be imported via static files, please reach out to us on [Discord](https://www.opensource.observer/discord) to coordinate hand-off. This path is predominantly used for [grant funding data](./funding-data.md).
7. (deprecated) [Airbyte](./airbyte.md): a modern ELT tool

We generally prefer to work with data partners that can help us regularly
index live data that can feed our daily data pipeline.
All data sources should be defined as
[software-defined assets](https://docs.dagster.io/concepts/assets/software-defined-assets) in our Dagster configuration.

ETL is the messiest, most high-touch part of the OSO data pipeline.
Please reach out to us for help on
[Discord](https://www.opensource.observer/discord).
We will happily work with you to get it working.
