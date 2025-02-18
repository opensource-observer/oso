# py_oso

_WARNING: THIS IS A WORK IN PROGRESS_

`py_oso` is a Python package for fetching models and metrics from OSO. This package provides an easy-to-use interface to interact with oso and retrieve valuable data for analysis and monitoring.

## Current Features

- Execute custom SQL queries for analyzing the OSO dataset

## Installation

You can install `py_oso` using pip:

```bash
pip install py_oso
```

## Usage

Here is a basic example of how to use `py_oso`:

```python
from py_oso import Client

# Initialize the client
os.environ["OSO_API_KEY"] = 'your_api_key'
client = Client()

# Fetch artifacts
query = "SELECT * FROM artifacts_v1 LIMIT 5"
artifacts = client.query(query)

print(artifacts)
```

## Documentation

For detailed documentation about the OSO dataset, please refer to the [official documentation](https://docs.opensource.observer/docs/integrate/datasets/).

## Future Plans

- Create DataFrame wrapper for creating SQL query from data transforms
