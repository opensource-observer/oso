---
title: Contribute Data
sidebar_position: 0
---

# Contribute Data

We're always looking for new data sources to integrate with OSO. Here are the current patterns for integrating new data sources:

- 💻 [Get started](./setup/index.md) - Setup your development environment with Dagster
- 🗂️ [BigQuery Public Datasets](./bigquery.md) - Preferred and easiest route for sharing a dataset
- 🗄️ [Database Replication](./database.md) - Provide access to your database for replication as an OSO dataset
- 📈 [GraphQL API Crawler](./graphql-api.md) - Automatically crawl any GraphQL API
- 🌐 [REST API Crawler](./rest-api.md) - Automatically crawl any REST API
- 📁 [Files into Google Cloud Storage (GCS)](./gcs.md) - Drop Parquet/CSV files in our GCS bucket for loading into OSO
- ⚙️ [Custom Dagster Assets](./dagster.md) - Write a custom Dagster asset for unique data sources
- 📜 Static Files - Coordinate hand-off for high-quality data via static files. This path is predominantly used for [grant funding data](./funding-data.md).

Reach out to us on [Discord](https://www.opensource.observer/discord) for help.

## Deprecated

- 🔁 [BigQuery Data Transfer Service](./bq-data-transfer.md) - Makes it easy to transfer from S3 to GCS into BigQuery
- ✈️ [Airbyte](./airbyte.md) - A modern ELT tool
