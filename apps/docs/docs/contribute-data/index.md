---
title: Contribute Data
sidebar_position: 0
---

# Contribute Data

We're always looking for new data sources to integrate with OSO. Here are the current patterns for integrating new data sources:

- 🗂️ [BigQuery Public Datasets](./bigquery.md) - Preferred and easiest route for maintaining a dataset
- 🗄️ [Database Replication](./database.md) - Provide access to your database for replication as an OSO dataset
- 🌐 [API Crawling](./api-crawling/index.md) - Crawl REST and GraphQL APIs easily by writing a plugin
- 📁 [Files into Google Cloud Storage (GCS)](./gcs.md) - Drop Parquet/CSV files in our GCS bucket for loading into BigQuery
- ⚙️ [Custom Dagster Assets](./dagster.md) - Write a custom Dagster asset for unique data sources
- 📜 Static Files - Coordinate hand-off for high-quality data via static files. This path is
  predominantly used for [grant funding data](./funding-data.md).
- 🚫 (deprecated) [Airbyte](./airbyte.md) - A modern ELT tool

Reach out to us on [Discord](https://www.opensource.observer/discord) for help.
