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
[![](https://mermaid.ink/img/pako:eNqFVU1P3DAQ_SuWT1nBtlKPe6gERVWpykcLpVJJD44zJC6OHcY2C0X8947jLNlsdiGXJPa88Zv3MpMnLm0JfMHn83luvPIaFiznZy0YdmEDSmBnhQO8B2QHKGvlQfqAkPPcdJDc3Gi7lLVAzy4Pc8PocqGoULQ1a0OhlbzO-YH0Fh3LTq2Zw0MtgvPqHmY5_5MQ8Qp0jKPYn_E-2inhPm4cCS-YkwqIp_OOvWdgKmVgPRxMmR66bGw-p2KuFCwp-HsAfMw5rX1k1tklFCkyZk-Bn6zxqIrggUVV-lhlSngAfCW4oWDtVqlJJXAehVfWbIJ-BMPuiIcCNzARrUpxG-rR1vV2K7pyB30GvVULmhQh2IlQhnWKnfeLI0njNWJKkK-2GK-x7EhUzgPuuTvdgKtnkxy9OCt3pNUaeq9L7afxhapi_Y_XWY9YCoTaklssO1RV5xGhZhswaZuWlC6ElzWddSjkLTm9WmZSh0iTZZeojJ1tyDOpNXlB5a5MWE-_tb6J5SVx78Fa3KYKdlNO8BNBHJXQ6h-8Dl2JlGDnaCW4t6m-JHsbtgMYTfn2kiU7llAAVlvtMC40gD7KTX5c0FepTMUS69SVIzN2ghPX9dbcoknX1MNrapkpcpR4a3_cIDlI2Yjy5_6RxY5SEty0PboZQaG_oGCibWmS9V1xBdSMeu8UHvy7v262DUkE49g7P2b98My-CBdQ7B201CJ2tuO0aVHr82E04IaBMTzRJt_nJEEjVElD_Sku59zX0NAnFwd7KfA2zu5nihPB24tHI_nCY4B9jjZUNV_cCO3oLbT0jcOREiRd87LaCvPb2uEdSkXdfpL-Id2vZJ9XGA_vcxIlwE82GM8XH57_A664BIU?type=png)](https://mermaid.live/edit#pako:eNqFVU1P3DAQ_SuWT1nBtlKPe6gERVWpykcLpVJJD44zJC6OHcY2C0X8947jLNlsdiGXJPa88Zv3MpMnLm0JfMHn83luvPIaFiznZy0YdmEDSmBnhQO8B2QHKGvlQfqAkPPcdJDc3Gi7lLVAzy4Pc8PocqGoULQ1a0OhlbzO-YH0Fh3LTq2Zw0MtgvPqHmY5_5MQ8Qp0jKPYn_E-2inhPm4cCS-YkwqIp_OOvWdgKmVgPRxMmR66bGw-p2KuFCwp-HsAfMw5rX1k1tklFCkyZk-Bn6zxqIrggUVV-lhlSngAfCW4oWDtVqlJJXAehVfWbIJ-BMPuiIcCNzARrUpxG-rR1vV2K7pyB30GvVULmhQh2IlQhnWKnfeLI0njNWJKkK-2GK-x7EhUzgPuuTvdgKtnkxy9OCt3pNUaeq9L7afxhapi_Y_XWY9YCoTaklssO1RV5xGhZhswaZuWlC6ElzWddSjkLTm9WmZSh0iTZZeojJ1tyDOpNXlB5a5MWE-_tb6J5SVx78Fa3KYKdlNO8BNBHJXQ6h-8Dl2JlGDnaCW4t6m-JHsbtgMYTfn2kiU7llAAVlvtMC40gD7KTX5c0FepTMUS69SVIzN2ghPX9dbcoknX1MNrapkpcpR4a3_cIDlI2Yjy5_6RxY5SEty0PboZQaG_oGCibWmS9V1xBdSMeu8UHvy7v262DUkE49g7P2b98My-CBdQ7B201CJ2tuO0aVHr82E04IaBMTzRJt_nJEEjVElD_Sku59zX0NAnFwd7KfA2zu5nihPB24tHI_nCY4B9jjZUNV_cCO3oLbT0jcOREiRd87LaCvPb2uEdSkXdfpL-Id2vZJ9XGA_vcxIlwE82GM8XH57_A664BIU)

## Major Components

The architecture has the following major components.

### Data Orchestration

Dagster is the central data orchestration system, which manages the entire pipeline,
from the data ingestion (e.g. via [dlt](https://docs.dagster.io/integrations/embedded-elt/dlt) connectors) to the [sqlmesh](https://github.com/opensource-observer/dagster-sqlmesh) pipeline.

You can see our public Dagster dashboard at
[https://dagster.opensource.observer/](https://dagster.opensource.observer/).

### Data Lakehouse

Currently all data is stored in managed Iceberg tables.

We also make heavy use of public datasets from
[Google BigQuery](https://cloud.google.com/bigquery/?hl=en).
To see all BigQuery datasets that you can subscribe to, check out our
[Data Overview](../integrate/datasets/index.mdx).

### sqlmesh pipeline

We use a [sqlmesh](https://sqlmesh.com/) pipeline to clean and normalize the data
into a universal event table and metrics. You can read more about our event model
[here](./event.md).

### Trino clusters

We maintain separate Trino clusters the operate over the Iceberg tables:

- Production pipeline cluster - a read-write cluster to run the sqlmesh pipeline
- Consumer query cluster - a read-only cluster to serve the API and `pyoso`

### API service

We use [Hasura](https://hasura.io/) to automatically generate
a GraphQL API from our consumer Trino cluster.
We then use an [Apollo Router](https://www.apollographql.com/docs/router/)
to service user queries to the public.
The API can be used by external developers to integrate data from OSO.
Rate limits or subscription pricing may apply to its usage depending
on the systems used. This also powers the OSO website.

### OSO Website

The OSO website is served at
[https://www.opensource.observer](https://www.opensource.observer).
This website provides an easy to use public view into the data.
We currently use [Next.js](https://nextjs.org/)
hosted by [Vercel](https://vercel.com/).

## Open Architecture for Open Source Data

The architecture is designed to be fully open to maximize open source collaboration.
With contributions and guidance from the community,
we want Open Source Observer to evolve as we better understand
what impact looks like in different domains.

All code is open source in our
[monorepo](https://github.com/opensource-observer/oso).
All data, including every stage in our pipeline, is publicly available via
[pyoso](../get-started/python.md).
All data orchestration is visible in our public
[Dagster dashboard](https://dagster.opensource.observer/).

You can read more about our open philosophy on our
[blog](https://kariba.substack.com/p/open-source-open-data-open-infra).
