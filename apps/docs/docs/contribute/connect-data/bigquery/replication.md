---
title: 🏗️ Using a BigQuery Data Transfer Service
sidebar_position: 2
---

import NextSteps from "../dagster-config.mdx"

BigQuery comes with a built-in data transfer service
for replicating datasets between BigQuery projects/regions,
from Amazon S3, and from various Google services.
In this guide, we'll copy an existing BigQuery dataset into the
`opensource-observer` Google Cloud project at a regular schedule.

If you already maintain a public dataset in
the US multi-region, you should simply make a dbt source
as shown in [this guide](./index.md).

## OSO Dataset Replication

:::warning
Coming soon... This section is a work in progress.
To track progress, see this
[GitHub issue](https://github.com/opensource-observer/oso/issues/1311).
:::

<NextSteps components={props.components}/>
