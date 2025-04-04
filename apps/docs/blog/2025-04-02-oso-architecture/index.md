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
