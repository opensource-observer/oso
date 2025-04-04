---
slug: oso-architecture-evolution
title: "OSO's Architecture Evolution"
authors: [ryscheng, ravenac95]
tags: [featured, development]
---

Over 2024, OSO's technical architecture went through several major
iterations to get to where it is now.
There are so many different ways to architect data infrastructure,
that the choices can be overwhelming.
Every platform will say they provide what you think you need,
and none of them will do everything you actually need.
In this post, we'll share the choices that OSO made along the way
and the pros and cons of each decision.

<!-- truncate -->

## Phase 1: A simple indexer

When we first started in late 2023, we had a short period of time to
get data together in time for our first big partnership,
[Optimism retro funding 3](../../blog/retropgf3-ecosystem-analysis/).
OSO's goal is to measure the impact of software in digital economies.
The first 2 datasets we would need to do that were
GitHub data (to see developer activity)
and blockchain data (to monitor end-user activity).

[![phase1](https://mermaid.ink/img/pako:eNqdU9uO2jAQ_RXLT6ASWmADNA-VtqyqrtSybNndSm364CQDuE3s1BcuRfz7juPAcmlf6jwkmTmeM3NmZktTmQGNaBAEsTDc5BCRmOIjKkssZrlcpQumDHl4HwuCR9tkrli5IKVNcp5-j-l1aqTSpDGWIoD1gllt-BKaMf3hb7hjNSiN2Ef3PvFksHSOG1hCLstzLxMs32hTIZhhZJpywETRcoCByPxHxUGCACt44rAir8m9BbWJKdreEanlChKPdJweOJLCKJ5YA8RJ8R_YVLFVDsqD9-n6C1-sIL8xBQ76JTAruceeyYkuLPKuBEGm0qoUyF2CBS0x9LEgPoKPf1xehuokTINr2h57iD1TmDrqhAQf6k_iYvMUTuWuGbB4hH6FhLCyxCYzw6UgjSfAtPJXY1ib9k_d_NtNzM1NxOSW-NxJ4yPTVrHmP2guCzmW6KS9L5q5U8uOZCOcN1mQW5HB2hGOsTcX6dVwT3edZcRN04V0h5msLa4hnx4mFdj9k8ZEajNXcBb9MIi0RQtQBeMZLtXWmWNqFlDgsLjFypj65ZZrhzhmjZxuREojoyy0qJJ2vqDRjOUa_2yJOcANZ9jA4mAtmfgmZbG_AhnHzfvsV7ja5BadK8ddh8SMQI2kFYZG3X5YBaDRlq5pNOi0w1541Q3D4WBw1e13WnRDo7DXDt8Oh_0eOjr9zqCza9E_FeOb9nAQ7p4B59RJfQ?type=png)](https://mermaid.live/edit#pako:eNqdU9uO2jAQ_RXLT6ASWmADNA-VtqyqrtSybNndSm364CQDuE3s1BcuRfz7juPAcmlf6jwkmTmeM3NmZktTmQGNaBAEsTDc5BCRmOIjKkssZrlcpQumDHl4HwuCR9tkrli5IKVNcp5-j-l1aqTSpDGWIoD1gllt-BKaMf3hb7hjNSiN2Ef3PvFksHSOG1hCLstzLxMs32hTIZhhZJpywETRcoCByPxHxUGCACt44rAir8m9BbWJKdreEanlChKPdJweOJLCKJ5YA8RJ8R_YVLFVDsqD9-n6C1-sIL8xBQ76JTAruceeyYkuLPKuBEGm0qoUyF2CBS0x9LEgPoKPf1xehuokTINr2h57iD1TmDrqhAQf6k_iYvMUTuWuGbB4hH6FhLCyxCYzw6UgjSfAtPJXY1ib9k_d_NtNzM1NxOSW-NxJ4yPTVrHmP2guCzmW6KS9L5q5U8uOZCOcN1mQW5HB2hGOsTcX6dVwT3edZcRN04V0h5msLa4hnx4mFdj9k8ZEajNXcBb9MIi0RQtQBeMZLtXWmWNqFlDgsLjFypj65ZZrhzhmjZxuREojoyy0qJJ2vqDRjOUa_2yJOcANZ9jA4mAtmfgmZbG_AhnHzfvsV7ja5BadK8ddh8SMQI2kFYZG3X5YBaDRlq5pNOi0w1541Q3D4WBw1e13WnRDo7DXDt8Oh_0eOjr9zqCza9E_FeOb9nAQ7p4B59RJfQ)

We took inspiration from how many indexers are built,
from [The Graph](https://thegraph.com/)
and [DefiLlama](https://defillama.com/) on the
blockchain data side,
to [Augur](https://github.com/chaoss/augur)
and [Grimoire](https://github.com/chaoss/grimoirelab)
on the GitHub data side.

In this architecture, we ran a simple
Node.js web server backed by a Postgres database.
We tried to use as much free infrastructure as we could,
including the [Vercel](https://vercel.com/) and
[Supabase](https://supabase.com/) free tiers.
We also wrapped the data fetching logic in a Node.js CLI,
so that we could run jobs from [GitHub actions](https://github.com/features/actions)
to take advantage of the free compute minutes available to open source projects.

**_Pros_**

- Simple and fast to build
- Low operational costs (free)
- Leverage the rich web development ecosystem

**_Cons_**

- Inflexible and difficult to do data science
- Lots of custom code to scrape APIs
- Difficult to trace data quality issues

One of the cool technologies that we discovered at this time
was [Hasura](https://hasura.io/),
which automatically turned any Postgres database into a GraphQL API.
Eventually, we replaced Postgres with
[Timescale](https://www.timescale.com/)
in order to more efficiently store and query time series events.

The problem with the initial architecture was that we
both aggregated too much, and too little to be effective.
We quickly outgrew simple aggregations
and wanted to run more sophisticated queries, which would not
perform well at request time.
Any time we wanted to introduce a new metric, it required
a large amount of engineering work and reindexing all of the data.

For example, we wanted to count the number of distinct active developers
across all repos in a project.
When we first started, we stored data bucketing events by day to be
storage efficient, which lost the data fidelity needed to compute something like this.
We learned the hard way, as countless others before us,
that [ETL](https://en.wikipedia.org/wiki/Extract%2C_transform%2C_load)
processes are not great for data science.
It was time to transition to an
[ELT](https://aws.amazon.com/compare/the-difference-between-etl-and-elt/) process.

![ELT](https://images.ctfassets.net/xnqwd8kotbaj/62wFnQhpt5STjuOyNPogDa/b1436e9c5a8f18219e6db93b7d55d5d2/data-pipeline_glossary.png)

## Phase 2: Adding dbt and BigQuery

Enter data warehouses, like Snowflake, Databricks, and BigQuery.
By storing all of the raw source data in a data warehouse,
it makes it trivial to dynamically run any arbitrary queries on top.
We can define a sequences of transformations in our data pipeline.
We chose to use [dbt](https://www.getdbt.com/),
which is still considered best-in-class for this workload.
If we changed any data model, the pipeline should be smart enough
to only recompute models downstream from it.
It was also smart enough to incrementally run models on fresh data.

We also decided to build on top of Google BigQuery,
which already had the 2 main public datasets we needed at the time for free,
GitHub and Optimism blockchain data.
It was also the only major data warehouse that supported retail users.
Anyone with a Google account could query the raw data or our data models,
up to 1TB for free every month.
As a first-stage filter, we would filter down the raw data sources
to just the relevant events for a small subset of projects.
Then, we'd normalize everything in our own semantic model
of [artifacts, projects, collections, and events](../../docs/references/).
Metrics were then computed against a universal event table,
each represented by its own data model.

[![](https://mermaid.ink/img/pako:eNp9VNty2jAQ_RWNnmAKtE5ioH7oTBPaaTu5kJKmM437INsbW62RXF1CSIZ_z8oyJgFS8YC8Oquze3a1jzSVGdCI9vv9WBhuSohITPEnakssbku5SAumDLk6jgXBpW2SK1YVpLJJydObmH5MjVSadM6l6MN9waw2_A66Mf3tPdyyGpRG7A_3_-Ikgzt3MGGGkU8i5wK2EUywcqlNi5qlHDBYtLQwEJnf1Dyk38csrjksyFtyaUEtY4q2D0RquYDEIx2vB24hWMU9Ys3rUSdSGMUTa4DMLk8beCrnFVoSZtJin9N3K8g_vJ6DbjwWTEEhMUwP39IU6THLiwoEmUmrUiAXCWZ0B6pOdaPJpgq8ghJFC9bqTBvDCwndkiotQBvFDJfCwb_J5KWRdCYs1wZUd8e5Dfum0_C0FtI55nmtIbp1t_yeC3TTSE0qJVPQum6aLDG7bM-9vJBnDMPirOQPsF_InUC939RTvVqutnk2n74Fdlsjw6wT9pxvi2s3xo3LnsrdKuwo5EZZPjdb4mrNU9C7xas7F6E_ISGsqvDlNSW7BmyT8s053JvBH93d54npuGc6_Up8L5HOF6atYt1XaP7_LNqH2yTnOuLi9GpKJo2BdKZSm1yB3mqI9pVuOn-zw0Pao3NQc8YzHEmPzhxTU8Ac5XRjKWPqrxtNK8Qxa-RsKVIaGWWhR5W0eUGjW1Zq_LIVBgcTzlDpeWutmPgl5XztAhnHuXXmB2A9B3s0V467uRIjAnUirTA0Cg6C-gIaPdJ7Go2CQXgYHh2E4Xg0OjoY4uGSRuHhIHw_Hg8P8SAYBqNg1aMPNeO7wXgUrp4A-sasPA?type=png)](https://mermaid.live/edit#pako:eNp9VNty2jAQ_RWNnmAKtE5ioH7oTBPaaTu5kJKmM437INsbW62RXF1CSIZ_z8oyJgFS8YC8Oquze3a1jzSVGdCI9vv9WBhuSohITPEnakssbku5SAumDLk6jgXBpW2SK1YVpLJJydObmH5MjVSadM6l6MN9waw2_A66Mf3tPdyyGpRG7A_3_-Ikgzt3MGGGkU8i5wK2EUywcqlNi5qlHDBYtLQwEJnf1Dyk38csrjksyFtyaUEtY4q2D0RquYDEIx2vB24hWMU9Ys3rUSdSGMUTa4DMLk8beCrnFVoSZtJin9N3K8g_vJ6DbjwWTEEhMUwP39IU6THLiwoEmUmrUiAXCWZ0B6pOdaPJpgq8ghJFC9bqTBvDCwndkiotQBvFDJfCwb_J5KWRdCYs1wZUd8e5Dfum0_C0FtI55nmtIbp1t_yeC3TTSE0qJVPQum6aLDG7bM-9vJBnDMPirOQPsF_InUC939RTvVqutnk2n74Fdlsjw6wT9pxvi2s3xo3LnsrdKuwo5EZZPjdb4mrNU9C7xas7F6E_ISGsqvDlNSW7BmyT8s053JvBH93d54npuGc6_Up8L5HOF6atYt1XaP7_LNqH2yTnOuLi9GpKJo2BdKZSm1yB3mqI9pVuOn-zw0Pao3NQc8YzHEmPzhxTU8Ac5XRjKWPqrxtNK8Qxa-RsKVIaGWWhR5W0eUGjW1Zq_LIVBgcTzlDpeWutmPgl5XztAhnHuXXmB2A9B3s0V467uRIjAnUirTA0Cg6C-gIaPdJ7Go2CQXgYHh2E4Xg0OjoY4uGSRuHhIHw_Hg8P8SAYBqNg1aMPNeO7wXgUrp4A-sasPA)

**_Pros_**

- Simple and low setup costs
- Leverage the rich public data ecosystem of BigQuery
- Easily share data with any Google user
- Integrates easily with Kaggle

**_Cons_**

- Very high computation costs
- Proprietary technical stack
- Jinja macros

We'll address the cons
[later](#phase-6-replacing-dbtbigquery-with-sqlmeshtrinoiceberg).
For now, this was a huge step up in our ability
to experiment with different data models.
At the end of the pipeline, we materialize our
mart models into the same Postgres database for serving the API.

## Phase 3: Replacing GitHub actions with Dagster

At this point, we were still using GitHub actions
to orchestrate all of our data jobs.
The problem here was when things went wrong (which happened a lot),
it was very difficult to find the exact failure in the logs.
It was also difficult to tell how fresh any particular data model was,
and we had no capacity to materialize a single model.
Instead, we only had 1 job that would run the entire pipeline.

By this time, we were racing to get metrics ready for Optimism retro funding 4,
the first time our metrics would directly impact the flow of funding.
Debugging a stable pipeline was the top priority.
We were also partnering with [Goldsky](https://goldsky.com/)
to ingest our own blockchain traces from 7 networks in the Superchain,
releasing them as a public dataset.

![dagster](./dagster_assets.png)

In order to facilitate better debugging,
we moved all of our data orchestration to
[Dagster](https://dagster.io/),
which allowed us to visualize the entire data pipeline,
monitor data jobs, data freshness, and debug individual failing models.

## Phase 4: Replacing Postgres with Clickhouse

By this point, our metrics were derived from over 50TB+ of raw data.
Even the mart models being served from the API were over 100GB+ in size.
The Postgres database we used for serving was struggling to keep up with queries,
even with basic lookups.
The breaking point came when the job to create indices kept failing
for our larger tables (e.g. `artifacts_by_project_v1`).

We originally chose Postgres as the safe, most common option,
but it was increasingly clear its limitations as a
[OLTP](https://en.wikipedia.org/wiki/Online_transaction_processing)
database. We wanted to switch to an
[OLAP](https://en.wikipedia.org/wiki/Online_analytical_processing)
database, optimized for analytics queries.
After evaluating some options,
we ended up choosing [Clickhouse](https://clickhouse.com/),
which has built a reputation for low-latency snappy
analytics queries, suitable for frontends.

## Phase 5: Replacing custom indexing with dlt

We quickly outgrew what we could do with just the available public datasets.
Beyond establishing our own ELT ingest for Superchain data,
we also needed to ingest
[Farcaster](https://www.farcaster.xyz/),
[Gitcoin](https://www.gitcoin.co/),
[OpenRank](https://openrank.com/), and
[EAS](https://attest.org/) data.

We evaluated a number of different data movement tools,
with very limited success,
including:
[Airbyte](https://airbyte.com/),
[CloudQuery](https://www.cloudquery.io/),
[Meltano](https://meltano.com/),
[BigQuery Data Transfer Service](https://cloud.google.com/bigquery/docs/dts-introduction).
Sometimes, we wanted to replicate an existing dataset
from S3 or Postgres.
Sometimes, we wanted to crawl an API, which could be REST or GraphQL.
Often times these different solutions would fail for
a [variety](https://github.com/opensource-observer/oso/issues?q=is%3Aissue%20state%3Aclosed%20cloudquery%20)
of [reasons](https://github.com/opensource-observer/oso/issues?q=is%3Aissue%20state%3Aclosed%20airbyte%20).

[![](https://mermaid.ink/img/pako:eNp9VNty2jAQ_RWNnmACtCRxoH7oTBLaaTu5kNKmM8V9kO0NVmMkV5cAyfDvXdnGTmwS84C8Ose7e3S0TzSSMVCf9vv9QBhuUvBJQPEn8kgg7lK5ihKmDPlxFgiCj7bhQrEsIZkNUx7NA3oaGak06VxJ0Yd1wqw2_AG6Af1TMNxjNSiN2J_u_8VODA9uY8IMI5_EggtoIphg6UabCjWLOGCxGKlgIOJikech_T52ccthRd6RGwtqE1CMfSRSyxWEBdLlLYANBMt4E3EuhVE8tAaIE6zEchHDGlQB3hXZIsxuLkp8JJcZRkJmomQf6bsV5B_WwkGXjBVTkEjsqYA3DgBrRUmuMxBkJq2KgFyH2P4DluR0qQWsj4xnkKLCw52U0zLwQm_3SBUloI1ihkvh4N9k-DJIOhO20AZUt0UuhdkliWSaQumRODVtfNXmvFNSqgjpnPFFfkBI6zZ4zwWdl-dIMiUj0LrIFppXq2sdVIyJ9-u-L19Bv2QoAGcpf4S3qXVDOW9aFPmqMSpP16-FM9uOdWWH7Hm-Rq52jTVlj0fuFEqCuVHQz-WSOFfxCHTbJvmFQugvCAnLMhwIpTluAQ2ZHlzB2gz-6u4-Jrbjpsf0KylcSzpfmLaKHZxm6BjZfSXb25e2Gitlj85S1xenUzIpA6RzjlXe5wI1PFVNkfqy1SvcpD26BLVkPMaR-eTCATUJLFFXNzZjpu7d6NwijlkjZxsRUd8oCz2qpF0k1L9jqcY3m2F5MOEMJV9W0YyJ31IudxSIOd6Zy2JA53O6RxfK5S4_iRWBOpdWGOp7o5xP_Se6pv5oOPCOvONDzxuPRseHJ8Me3SDmaOB9GI9PjnBjeDIcDbc9-pgnfD8Yj7ztfxhf3UI?type=png)](https://mermaid.live/edit#pako:eNp9VNty2jAQ_RWNnmACtCRxoH7oTBLaaTu5kNKmM8V9kO0NVmMkV5cAyfDvXdnGTmwS84C8Ose7e3S0TzSSMVCf9vv9QBhuUvBJQPEn8kgg7lK5ihKmDPlxFgiCj7bhQrEsIZkNUx7NA3oaGak06VxJ0Yd1wqw2_AG6Af1TMNxjNSiN2J_u_8VODA9uY8IMI5_EggtoIphg6UabCjWLOGCxGKlgIOJikech_T52ccthRd6RGwtqE1CMfSRSyxWEBdLlLYANBMt4E3EuhVE8tAaIE6zEchHDGlQB3hXZIsxuLkp8JJcZRkJmomQf6bsV5B_WwkGXjBVTkEjsqYA3DgBrRUmuMxBkJq2KgFyH2P4DluR0qQWsj4xnkKLCw52U0zLwQm_3SBUloI1ihkvh4N9k-DJIOhO20AZUt0UuhdkliWSaQumRODVtfNXmvFNSqgjpnPFFfkBI6zZ4zwWdl-dIMiUj0LrIFppXq2sdVIyJ9-u-L19Bv2QoAGcpf4S3qXVDOW9aFPmqMSpP16-FM9uOdWWH7Hm-Rq52jTVlj0fuFEqCuVHQz-WSOFfxCHTbJvmFQugvCAnLMhwIpTluAQ2ZHlzB2gz-6u4-Jrbjpsf0KylcSzpfmLaKHZxm6BjZfSXb25e2Gitlj85S1xenUzIpA6RzjlXe5wI1PFVNkfqy1SvcpD26BLVkPMaR-eTCATUJLFFXNzZjpu7d6NwijlkjZxsRUd8oCz2qpF0k1L9jqcY3m2F5MOEMJV9W0YyJ31IudxSIOd6Zy2JA53O6RxfK5S4_iRWBOpdWGOp7o5xP_Se6pv5oOPCOvONDzxuPRseHJ8Me3SDmaOB9GI9PjnBjeDIcDbc9-pgnfD8Yj7ztfxhf3UI)

With the new Dagster setup,
we decided to just stick with Dagster
[embedded-elt](https://docs.dagster.io/integrations/libraries/embedded-elt),
which has built-in support for
[dlt](https://dlthub.com/).
It has satisfied every use case we've had so far,
and we've never looked back.

## Phase 5: Running sqlmesh on Clickhouse

Around August 2024, we hit a major roadblock with dbt and BigQuery.
Up until now, we were just computing metrics
at the current date (e.g. new active contributors to a project within the last 6 months).
What if we wanted to see the full time series of _any_ metric
for _any_ period of time?
This would be incredibly powerful, not just to show time-series graphs
in a dashboard.
It would be the fundamental underpinning of any causal inference
analysis to understand whether _any_ funding system is driving real outcomes.

In order to calculate time-series metrics,
we evaluated a number of metric semantic layers,
including
[Cube](https://cube.dev/) and
[MetricFlow](https://docs.getdbt.com/docs/build/about-metricflow).
However neither supported what we thought was the simplest
tablestakes metric:
"How many unique active users/developers churned between any 2 months?"

In order to perform this query, we'd need to mark each unique user/developer
by their activity in a 30-day rolling window.
Then we'd aggregate by artifact/project/collection, the number of unique
users/developers in a 30-day rolling window.
Then we'd compare 2 subsequent months in a rolling window to determine the changes (churn).

[![](https://mermaid.ink/img/pako:eNqVVdty2jAQ_RWNnmACtJA4ED90Jpd22k4upLTpTOM-yPYGq7ElR5cAyeTfu7INBDC0MQ_Yq3N8ds_Kq2cayRioT9vtdiAMNyn4JKD4E0UkEHepnEQJU4Z8PwkEwUvbcKxYnpDchimPbgN6HBmpNGlcStGGacKsNvwRmgH9XTLcZTUojdgf7n9lJYZHt3DGDCMfxZgLWEcwwdKZNgvUKOKAyWJkAQMRlzeFDmm3sYobDhPyjlxbULOAYuwDkVpOICyRTrcEriFYztcRp1IYxUNrgDjDKiwXMUxBleB5khuE0fV5hY9klmMkZCZK6kjfrCAPmAsHXTEmTEEisaYSvtYAzBUtucpBkJG0KgJyFWL5j5iS82Vp4LJlPIcUHe4i74JxQQo_h1V0xXR3SRUloI1ihkvhOF9luBokjTM21gZUc4NcuTNvWiTTFKqNEqdmE7-o9bZRURYR0jjh46JLSGuu8V67els1k-RKRqB1qRaardltdCtG4Xrz6_RK-gVDAzhL-RPspi4LKnjDMsmtu2OxsZeP_yPuSgiZ096xA3po1SeFdaPAW3ZB7427YJ6Ma-rV-fGw0HIB0jjF6XFf2FHTVf2QZqDrG1qtbRers7ci1ar828kt7SinxeYU2dmCu8r21x1wny2PQG-aX0wshP6EkLA8R88qy28Av_h07xKmpvNHN-uYmJsbz8MvpBwLpPGZaavY3nGOX6NsblHbPRVXxu1yKi3vcJG2aAYqYzzGs-XZhQNqEsjQWHe-xEzduzPmBXHMGjmaiYj6RlloUSXtOKH-HUs1PtkcrYQzztC6bBHNmfglZTanQMxxrlyUJ1lxoLXoWDnt6pWYEahTaYWh_lFBp_4znVK_3-14-95Bz_MG_f5B77DbojPqe_sd72gwONzHhe5ht999adGnQu99Z9D3Xv4C0NI5Ag?type=png)](https://mermaid.live/edit#pako:eNqVVdty2jAQ_RWNnmACtJA4ED90Jpd22k4upLTpTOM-yPYGq7ElR5cAyeTfu7INBDC0MQ_Yq3N8ds_Kq2cayRioT9vtdiAMNyn4JKD4E0UkEHepnEQJU4Z8PwkEwUvbcKxYnpDchimPbgN6HBmpNGlcStGGacKsNvwRmgH9XTLcZTUojdgf7n9lJYZHt3DGDCMfxZgLWEcwwdKZNgvUKOKAyWJkAQMRlzeFDmm3sYobDhPyjlxbULOAYuwDkVpOICyRTrcEriFYztcRp1IYxUNrgDjDKiwXMUxBleB5khuE0fV5hY9klmMkZCZK6kjfrCAPmAsHXTEmTEEisaYSvtYAzBUtucpBkJG0KgJyFWL5j5iS82Vp4LJlPIcUHe4i74JxQQo_h1V0xXR3SRUloI1ihkvhOF9luBokjTM21gZUc4NcuTNvWiTTFKqNEqdmE7-o9bZRURYR0jjh46JLSGuu8V67els1k-RKRqB1qRaardltdCtG4Xrz6_RK-gVDAzhL-RPspi4LKnjDMsmtu2OxsZeP_yPuSgiZ096xA3po1SeFdaPAW3ZB7427YJ6Ma-rV-fGw0HIB0jjF6XFf2FHTVf2QZqDrG1qtbRers7ci1ar828kt7SinxeYU2dmCu8r21x1wny2PQG-aX0wshP6EkLA8R88qy28Av_h07xKmpvNHN-uYmJsbz8MvpBwLpPGZaavY3nGOX6NsblHbPRVXxu1yKi3vcJG2aAYqYzzGs-XZhQNqEsjQWHe-xEzduzPmBXHMGjmaiYj6RlloUSXtOKH-HUs1PtkcrYQzztC6bBHNmfglZTanQMxxrlyUJ1lxoLXoWDnt6pWYEahTaYWh_lFBp_4znVK_3-14-95Bz_MG_f5B77DbojPqe_sd72gwONzHhe5ht999adGnQu99Z9D3Xv4C0NI5Ag)

Instead, we ended up writing our own semantic layer metrics factory
on top of [sqlmesh](https://sqlmesh.com/).
sqlmesh is a drop-in replacement for dbt, with a number of additional powerful
features, including Python macros (bye bye Jinja),
automatic translation between SQL dialects,
and the ability to auto-matically generate new models using Python.
These features were the fundamental unlock that enabled us to build our own
semantic layer and metrics system.
We built so much on the bleeding edge of metrics
that the team behind sqlmesh invited us to speak at their annual
[Tobiko conference](https://groupby.tobikodata.com/).

Our initial experiments ran the metrics pipeline on a separate
Clickhouse cluster, so that we could continue supporting the existing
mature dbt/BigQuery pipeline.
The experiment convinced us of 2 things:

1. sqlmesh is the future of data transformation
2. Clickhouse is great for serving, but too slow/costly for the backend pipeline

## Phase 6: Replacing dbt/BigQuery with sqlmesh/Trino/Iceberg

By now we were committed to fully transitioning our entire pipeline to sqlmesh.
However, our cloud bills were becoming astronomical.
On certain days when we ran a full pipeline refresh,
our 1-day cloud bill would be >$1000.
We needed to find a more cost-effective and scalable solution.

We decided to rip off the band-aid and do a major transition
to an auto-scaling Trino cluster while transitioning to sqlmesh.
We'd hit 3 birds with 1 stone: decentralizing our infra,
supporting time-series metrics on sqlmesh, and reducing our cloud costs
all in 1 go, at the cost of instability for months.

[![](https://mermaid.ink/img/pako:eNqFVdtS2zAQ_RWNnpwhSQkQEvLQGS7TKR0uaaF0prgPsrzYKrbk6kISGP69K9shFyfgPMRe7VntnqNdvVCuYqAj2ul0QmmFzWBEQoo_WVpC-ZCpCU-ZtuT2JJQEH-OiRLMiJYWLMsHvQ3rMrdKGBFdKdmCaMmeseIJWSP9UCP84A9qg70__v7ISw5NfOGOWEcMFYBrGGvKJgEyEhGV3kHH1UkYjnQ7meidggs7fHehZSNH2mSijJhBVnj565XiqpNUichaIL7r2FTKGKeh3nHN0zsw8tOYpGKuZFUqug344Sf5hHgLMIhNWiMpvjT1cwqqvC5DkRjnNgVxHWNUT5uLLXfCz4FsUkCEjCLtkQpKSsXFtXKHUPyuZIuSbilZtJDhjibGgd8y_LAeTthoxanLm6nCVZVBrHWe26R-JxNc_uw9qxIRpSBWqRYITkZQaIaq1BuMqL5DpiFme4l4njD-i0nMz4ZnzaZLgVgupWmv0NGqttMBy5yIsh99YX0PyGHOvwRl7rCrYnnIFv2SYo2CZeIb3oXOSKthYKw7m41Tfgn0M2wL0oly8RQnOOUSgkw1yqIwVnoGIGX_Wri-Ox-VZ898kOMWefyxjNPXnShqXg7ZeKITe4HkWMiFVvVU_r8i4FVxVudzUW9hc46WpwnI1C2g5SRafVZ82N90M3ua9UsHGFn7QeMhwb-TmS_1KfNMLDqbZweUYQ9dfEBFWFEh83bh3gPMi27mCqe3-Na1NSEzQT-bxOamGCgm-MuM0exeE223gYGmGrQzhxVBbvOEibVPkIGcixnvlxZtDalPIURB_t8RMP_r75RX9mLPqZiY5HVntoE21cklKRw8sM_jlPPVwJhhyl79ZCyZ_K5XPIRALHEiX1S1WXmZtmmi_dx0SMwJ9qpy0dLS3e1QGoKMXOqWjQa_b3-8f7PX7w8HgYO-w16YzOurvd_tHw-HhPi70DnuD3mubPpc77naHg_7rf_VROPc?type=png)](https://mermaid.live/edit#pako:eNqFVdtS2zAQ_RWNnpwhSQkQEvLQGS7TKR0uaaF0prgPsrzYKrbk6kISGP69K9shFyfgPMRe7VntnqNdvVCuYqAj2ul0QmmFzWBEQoo_WVpC-ZCpCU-ZtuT2JJQEH-OiRLMiJYWLMsHvQ3rMrdKGBFdKdmCaMmeseIJWSP9UCP84A9qg70__v7ISw5NfOGOWEcMFYBrGGvKJgEyEhGV3kHH1UkYjnQ7meidggs7fHehZSNH2mSijJhBVnj565XiqpNUichaIL7r2FTKGKeh3nHN0zsw8tOYpGKuZFUqug344Sf5hHgLMIhNWiMpvjT1cwqqvC5DkRjnNgVxHWNUT5uLLXfCz4FsUkCEjCLtkQpKSsXFtXKHUPyuZIuSbilZtJDhjibGgd8y_LAeTthoxanLm6nCVZVBrHWe26R-JxNc_uw9qxIRpSBWqRYITkZQaIaq1BuMqL5DpiFme4l4njD-i0nMz4ZnzaZLgVgupWmv0NGqttMBy5yIsh99YX0PyGHOvwRl7rCrYnnIFv2SYo2CZeIb3oXOSKthYKw7m41Tfgn0M2wL0oly8RQnOOUSgkw1yqIwVnoGIGX_Wri-Ox-VZ898kOMWefyxjNPXnShqXg7ZeKITe4HkWMiFVvVU_r8i4FVxVudzUW9hc46WpwnI1C2g5SRafVZ82N90M3ua9UsHGFn7QeMhwb-TmS_1KfNMLDqbZweUYQ9dfEBFWFEh83bh3gPMi27mCqe3-Na1NSEzQT-bxOamGCgm-MuM0exeE223gYGmGrQzhxVBbvOEibVPkIGcixnvlxZtDalPIURB_t8RMP_r75RX9mLPqZiY5HVntoE21cklKRw8sM_jlPPVwJhhyl79ZCyZ_K5XPIRALHEiX1S1WXmZtmmi_dx0SMwJ9qpy0dLS3e1QGoKMXOqWjQa_b3-8f7PX7w8HgYO-w16YzOurvd_tHw-HhPi70DnuD3mubPpc77naHg_7rf_VROPc)

After a painful Q1, we are excited to share the results of this refactor:

- We run all of our queries on an auto-scaling Trino cluster of spot instances.
  This makes it cheap enough to run calculate all our metrics as time-series for all time.
- We launched [`pyoso`](../../docs/get-started/python),
  which offers the community a generous quota to query the OSO data lake.
- We scanned over 1.2 PB across a 20-node cluster in the last month,
  preparing for Optimism retro funding.
- You can contribute both
  [data](../../docs/contribute-data/)
  and [models](../../docs/contribute-models/)
  to the OSO data lake to take advantage of this community resource.

Let's analyze software impact together!

## Summary

Here's where we ended up after a year of exploring DataOps tooling:

- For cloud infrastructure: [Google Cloud](https://cloud.google.com/)
- For data orchestration: [Dagster](https://dagster.io/)
- For data transformations: [sqlmesh](https://sqlmesh.com/)
- For data ingest: [dlt](https://dlthub.com/)
- For data lake tables: [Apache Iceberg](https://iceberg.apache.org/)
- For OLAP database: [Clickhouse](https://clickhouse.com/)
- For OLTP database: [Supabase](https://supabase.com/)
- For GraphQL APIs: [Hasura](https://hasura.io/)
- For low-code frontend builder: [Plasmic](https://plasmic.app?ref=ryscheng)
- For frontend framework: [Next.js](https://nextjs.org/)
- For frontend hosting: [Vercel](https://vercel.com/)
