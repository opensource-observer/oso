---
slug: introducing-pyoso
title: "Introducing Pyoso: our new Python library for data scientists"
authors: [ccerv1, icarog]
tags: [data science, analytics, python]
image: ./pyoso-cover.png
---

We're excited to introduce **Pyoso**, a new Python library that makes it easy to query and analyze open source software data and metrics from OSO. Whether you're a data scientist, researcher, or builder, Pyoso gives you direct access to all our production data sets from your favorite analysis environment.

No need to manage infrastructure or wrangle database credentials. Just install the package, authenticate with [your free API key](https://www.opensource.observer/settings/api), and start querying!

<!-- truncate -->

## Why we built Pyoso

At Kariba, we've been working with a growing network of [Impact Data Scientists](../../blog/impact-data-scientists) to analyze the health and impact of open source ecosystems. Until now, most of that work required connecting to BigQuery or running a playground version of our database from the command line. We wanted to make it easier for anyone to get started with OSO data - especially those who live in Jupyter notebooks.

(We also moved our production database off of BigQuery. You shouldn't care where the data lives. You should just be able to query it!)

Pyoso is a lightweight wrapper around our data lake that lets you write SQL queries and get back pandas DataFrames. It handles authentication, retries, and pagination under the hood. You can use it to explore project metrics, analyze funding flows, map software dependencies, and more.

You can install it with:

```bash
pip install pyoso
```

Here's a quick example:

```python
from pyoso import Client

client = Client(api_key="your_api_key")

query = "SELECT * FROM projects_v1 LIMIT 5"
df = client.to_pandas(query)

print(df)
```

Generate your API key [here](https://www.opensource.observer/settings/api).

## What you can do with it

Pyoso gives you access to every model in the OSO data lake. That includes:

- Project and collection directories (e.g. all projects, all GitHub repos owned by a project)
- Repo metadata (e.g. name, license, language, age)
- Project-level metrics (e.g. monthly active developers, dailly active users, commits, issues)
- Funding history (e.g. Gitcoin, Optimism, Open Collective)
- Software dependencies (e.g. SBOMs, package maintainers)
- Decentralized social networks (e.g. Farcaster, Lens)
- Developer graphs and social networks

We've published a set of [tutorials](../../docs/tutorials) to help you get started:

- [View a collection of projects](../../docs/tutorials/collection-view)
- [Deep dive into a project](../../docs/tutorials/project-deepdive)
- [Map software dependencies](../../docs/tutorials/dependencies)
- [Analyze funding histories](../../docs/tutorials/funding-data)
- [Create a network graph](../../docs/tutorials/network-graph)

Each tutorial includes copy-pasteable code snippets and example queries.

## What's next

We're just getting started. In the coming months, we'll be adding support for:

- Parameterized queries
- Hooking up LLMs to the data lake
- Integration with visualization tools like Hex and Streamlit
- More helper functions for common queries

Regardless of whether you're an aspiring data scientist or seasoned SQL monkey, we'd love for you to try it out and show off your creations. You can also join our [Discord](https://www.opensource.observer/discord) to connect with other contributors and share what you're building.

To learn more, check out the [Pyoso docs](../../docs/get-started/python).

![pyoso-meme](./pyoso-meme.png)
