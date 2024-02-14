---
title: Overview
sidebar_position: 1
---

Start here to learn about different ways of contributing to OSO.

OSO is looking for contributions to add/update information about open source projects, to explore the data and generate useful insights, and to connect new data sources and build better tools on top of OSO.

If you are interested in joining the Data Collective, your first step is to apply [here](https://www.opensource.observer/data-collective). Membership is free but we want to keep the community close-knit and mission-aligned.

## Static Datasets

It might not be the sexiest form of contribution, but it's the most important. We need to make sure that the data we have is accurate and up to date. This is a great way to get started with OSO.

### Project Data

Anyone can add a new project or update project information by submitting a PR to the [OSS Directory](https://github.com/opensource-observer/oss-directory). For more information on how to contribute to the OSS Directory, check out our guide for adding and updating [Project Data](./project-data).

### Funding Data

We are also building a database of funding information for open source projects. This is a valuable starting point for anyone interested in the economics of open source. Anyone can add a new funding source or update funding information by submitting a PR. For more information on how to contribute, check out our guide for adding and updating [Funding Data](./funding-data).

## Impact Data Science

We are building the place to do impact data science for open source ecosystems. We know how hard it is to get clean data ready to analyze in a Jupyter Notebook or whatever you platform you prefer for doing exploratory data analysis and visualizations. We want to remove those barriers and grow a decentralized data science community that believes in open source, open data, and open infrastructure.

### dbt Transforms

We are maintaining a data warehouse on BigQuery that members of our data collective can access. You can make queries directly in BigQuery or from the command line. For recurring queries, we use dbt to transform the data in our warehouse and create materialized views. You can write dbt models in SQL to aggregate metrics in our data warehouse. For more information on how to contribute, check out the [dbt Transforms](./dbt-transforms) section.

### Impact Vectors

We are building a suite of **impact vectors** that can be used to compare the impact of different open source projects. We are looking for contributions to help us build a library of impact vectors. For more information on how to contribute, check out the [Impact Vectors](./impact-vectors) section.

### Jupyter Notebooks

We are curating a library of Jupyter notebooks that can be used to explore and visualize the data on OSO. We are looking for contributions to help us build a library of Jupyter notebooks in our [insights repo](https://github.com/opensource-observer/insights). For more information on how to contribute, check out the [Jupyter Notebooks](./jupyter-notebooks) section.

## Data Engineering

You have ideas for new data sources and want to help us connect them? You see a world of possible integrations and want to help other developers build on top of OSO? You believe in truly open infra and want to help us break down the cost barriers and complexity of running a data pipeline? Our [OSO mono repo](https://github.com/opensource-observer/oso) is the place for data engineers who want to contribute to our core mission.

### CloudQuery Plugins

We are using CloudQuery to connect new data sources to OSO. We are looking for contributors to create plugins that bring more interesting datasets to OSO. For more information on how to contribute, check out the [CloudQuery Plugins](./cloudquery-plugins) section.

### Airbyte Connectors

We also use Airbyte for creating OSO data oracles. For more information on how to contribute new connectors, check out the [Airbyte Connectors](./airbyte-connectors) section.
