---
title: "Access via Python"
sidebar_position: 1
---

The [OSO](https://www.opensource.observer/settings/api) API serves
queries on metrics and metadata about open source projects.
You can access the full data lake via our `pyoso` Python library.

Let's make your first query in under five minutes.

## Generate an API key

First, go to [www.opensource.observer](https://www.opensource.observer/login) and create a new account.

If you already have an account, [log in](https://www.opensource.observer/login). Then create a new personal API key:

1. Go to [Account settings](https://www.opensource.observer/settings/api)
2. In the "API Keys" section, click "+ New"
3. Give your key a label - this is just for you, usually to describe a key's purpose.
4. You should see your brand new key. **Immediately** save this value, as you'll **never** see it again after refreshing the page.
5. Click "Create" to save the key.

![generate API key](../integrate/generate-api-key.png)

## Install pyoso

You can install pyoso using pip:

```bash
pip install pyoso
```

For semantic modeling capabilities, you can install with the `semantic` extra:

```bash
pip install pyoso[semantic]
```

## Issue your first query

Here is a basic example of how to use pyoso to fetch data directly into a pandas DataFrame:

```python
import os
from pyoso import Client

# Initialize the client
os.environ["OSO_API_KEY"] = 'your_api_key'
client = Client()

# Fetch artifacts
query = "SELECT * FROM artifacts_v1 LIMIT 5"
artifacts = client.to_pandas(query)

print(artifacts)
```

## Inspecting Data Provenance

For more advanced use cases, the `client.query()` method returns a `QueryResponse` object that contains both the data and analytics metadata. This allows you to inspect the dependency tree of the data sources used in your query.

```python
import os
from pyoso import Client

# Initialize the client
os.environ["OSO_API_KEY"] = "your_api_key"
client = Client()

# Execute a query to get a QueryResponse object
query = "SELECT * FROM artifacts_v1 LIMIT 5"
response = client.query(query)

# You can still get the DataFrame as before
df = response.to_pandas()
print("\n--- Query Data ---")
print(df)

# Now, inspect the analytics to see the dependency tree
print("\n--- Data Dependency Tree ---")
response.analytics.print_tree()
```

This will output a tree structure showing how the final `artifacts_v1` table was constructed from its upstream dependencies, helping you understand the data's origin and freshness.

```

```
