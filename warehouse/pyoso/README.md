# pyoso

_WARNING: THIS IS A WORK IN PROGRESS_

`pyoso` is a Python package for fetching models and metrics from OSO. This package provides an easy-to-use interface to interact with oso and retrieve valuable data for analysis and monitoring.

## Features

- Execute custom SQL queries for analyzing the OSO dataset.
- Inspect data dependencies and freshness with an analytics tree.
- Semantic modeling layer to build and execute complex queries (optional).

## Installation

You can install `pyoso` using pip:

```bash
pip install pyoso
```

### Optional Semantic Modeling

For semantic modeling capabilities, you can install with the semantic extra:

```bash
pip install pyoso[semantic]
```

This will include the `oso_semantic` package for building semantic models and queries.

## Usage

Here is a basic example of how to use `pyoso` to fetch data directly into a pandas DataFrame:

```python
import os
from pyoso import Client

# Initialize the client with an API key
os.environ["OSO_API_KEY"] = 'your_api_key'
client = Client()

# Fetch artifacts
query = "SELECT * FROM artifacts_v1 LIMIT 5"
artifacts = client.to_pandas(query)

print(artifacts)
```

### Inspecting Data Dependencies

For more advanced use cases, the `client.query()` method returns a `QueryResponse` object that contains both the data and analytics metadata. This allows you to inspect the dependency tree of the data sources used in your query.

```python
import os
from pyoso.client import Client

# Initialize the client
os.environ["OSO_API_KEY"] = "your_api_key"
client = Client()

# Execute a query to get a QueryResponse object
query = "SELECT * FROM artifacts_v1 LIMIT 5"
response = client.query(query)

# You can still get the DataFrame as before
df = response.to_pandas()
print("---\nQuery Data ---")
print(df)

# Now, inspect the analytics to see the dependency tree
print("\n--- Data Dependency Tree ---")
response.analytics.print_tree()
```

This will output a tree structure showing how the final `artifacts_v1` table was constructed from its upstream dependencies, helping you understand the data's origin and freshness.

## Documentation

For detailed documentation about the OSO dataset, please refer to the [official documentation](https://docs.opensource.observer/docs/integrate/datasets/).

## Future Plans

- Create DataFrame wrapper for creating SQL query from data transforms
