---
title: Explore Ways of Contributing
sidebar_position: 1
---

# Contributor Pathways

Start here to learn about different ways of contributing to OSO.

OSO maintains an [ETL](https://en.wikipedia.org/wiki/Extract%2C_load%2C_transform) data pipeline that is continuously deployed from our [monorepo](https://github.com/opensource-observer/oso/). OSO is looking for contributions on all stages of this pipeline, including:

- **Produce**: add/update information about open source projects
  (e.g. via [oss-directory](https://github.com/opensource-observer/oss-directory))
- **Extract**: ingest new data sources (e.g. Open Collective, GitHub, npm, analytics)
- **Transform**: the raw data into impact metrics and impact vectors per project
- **Load**: the results into different OSO integrations
- **Data science**: share your analysis and insights with the OSO community!

If you are interested in joining the Data Collective, your first step is to apply [here](https://www.kariba.network/). Membership is free but we want to keep the community close-knit and mission-aligned.

---

## Produce New Datasets

It might not be the sexiest form of contribution, but it's the most important. We need to make sure that the data we have is accurate and up to date. This is a great way to get started with OSO.

### Project Data

In order to analyze any project, we must be able to enumerate everything related to the project. This includes the code repositories, published packages, treasury addresses, and deployments. Anyone can add a new project or update project information by submitting a PR to the [OSS Directory](https://github.com/opensource-observer/oss-directory). For more information on how to contribute to the OSS Directory, check out our guide for adding and updating [Project Data](./produce/project-data).

### Funding Data

We are also building a database of funding information for open source projects. This is a valuable starting point for anyone interested in the economics of open source. Anyone can add a new funding source or update funding information by submitting a PR. For more information on how to contribute, check out our guide for adding and updating [Funding Data](./produce/funding-data).

---

## Extract Existing Data Sources

Raw data is replicated into the data warehouse using data movement tools like [CloudQuery](https://cloudquery.io/) and [Airbyte](https://airbyte.com/).

### Connect a data source with an existing connector

If any existing [connector](https://airbyte.com/connectors) or [plugin](https://hub.cloudquery.io/plugins/source) exists for your data source, [connect your data source to OSO](./extract/connect-your-data).

### Develop a new connector plugin

If one of the existing plugins do not satisfy, and you can [write your own plugin](./extract/write-data-connector.md) (e.g. to pull from a custom API).

---

## Data Transformations

We are building the place to do impact data science for open source ecosystems. We know how hard it is to get clean data ready to analyze in a Jupyter Notebook or whatever you platform you prefer for doing exploratory data analysis and visualizations. We want to remove those barriers and grow a decentralized data science community that believes in open source, open data, and open infrastructure.

TODO: What is the difference between these two?

### Impact Metrics

We are maintaining a data warehouse of OSS Impact Metris on BigQuery that members of our data collective can access. You can make queries directly in BigQuery or from the command line. For recurring queries, we use dbt to transform the data in our warehouse and create materialized views. You can write dbt models in SQL to aggregate metrics in our data warehouse. For more information on how to contribute, check out the [Create Impact Metrics](./transform/create-impact-metrics) section.

### DBT Models

Our data warehouse relies on dbt for cleaning and analyzing the data we gather from various sources. You can contribute to our analyses directly by forking our repository and adding your own dbt models or helping to correct the models already there. Check out the [Adding DBT Models](./transform/adding-dbt-models) guide!

---

## Load Data Integrations

OSO impact metrics are loaded into different integrations, from a public BigQuery data set, to a hosted API service.
For more information, see the section on [integrations](../integrate/getting-started).

---

## Impact Data Science

### Impact Vectors

We are building a suite of **impact vectors** that can be used to compare the impact of different open source projects. We are looking for contributions to help us build a library of impact vectors. For more information on how to contribute, check out the [Analyze Impact Vectors](./data-science/analyze-impact-vectors) section.

### Data Science Notebooks

We are curating a library of Jupyter notebooks that can be used to explore and visualize the data on OSO. We are looking for contributions to help us build a library of Jupyter notebooks in our [insights repo](https://github.com/opensource-observer/insights). For more information on how to contribute, check out the [Data Science Notebooks](./data-science/notebooks) section.
