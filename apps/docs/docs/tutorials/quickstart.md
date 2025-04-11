---
title: Pyoso Quickstart
description: Get started with pyoso and common query patterns for our most popular models
sidebar_position: 2
---

This tutorial walks through the basics of using [pyoso](../get-started/python.md) to explore the OSO data lake. This tutorial is designed to be run locally in a Jupyter notebook. We also have guides for using pyoso in different notebook environments [here](../guides/notebooks/).

:::tip
You can follow along by forking our pyoso-quickstart Jupyter Notebook in the Insights Repo [here](https://github.com/opensource-observer/insights/blob/main/pyoso-quickstart.ipynb).
:::

## Setup

Open a notebook and install the required packages:

```python
! pip install pyoso
```

Then initialize your environment:

```python
import pandas as pd
from pyoso import Client

OSO_API_KEY = # add your key here or load from .env
client = Client(api_key=OSO_API_KEY)
```

If you don't have an API key, follow these steps [here](../get-started/python.md). Remember never to share your API key publicly.

Define a helper function for formatting arrays in SQL:

```python
def stringify(arr):
    return "'" + "','".join(arr) + "'"
```

## Explore Available Models

Get a preview of all available models:

```python
client.to_pandas("SELECT * FROM models_v0 LIMIT 5")
```

Get the list of stable production models:

```python
client.to_pandas("SELECT * FROM models_v0 WHERE model_name LIKE '%_v1'")
```

Get the list of less stable models:

```python
client.to_pandas("SELECT * FROM models_v0 WHERE model_name LIKE '%_v0'")
```

## Query Popular Models

Get a list of projects:

```python
client.to_pandas("SELECT * FROM projects_v1 LIMIT 5")
```

Look up a specific project:

```python
client.to_pandas("SELECT * FROM projects_v1 WHERE project_name = 'opensource-observer'")
```

Get all artifacts owned by a project:

```python
client.to_pandas("SELECT * FROM artifacts_by_project_v1 WHERE project_name = 'opensource-observer'")
```

Get available key metrics for OSO:

```python
client.to_pandas("""
  SELECT
    km.metric_id,
    m.metric_name,
    m.display_name,
    km.sample_date,
    km.amount,
    km.unit
  FROM key_metrics_by_project_v0 AS km
  JOIN metrics_v0 AS m ON m.metric_id = km.metric_id
  WHERE km.project_id = 'UuWbpo5bpL5QsYvlukUWNm2uE8HFjxQxzCM0e+HMZfk='
""")
```

Get a set of key metrics for a few projects:

```python
MY_PROJECTS = ['opensource-observer', 'huggingface', 'wevm']
MY_METRICS = ['GITHUB_stars_over_all_time', 'GITHUB_forks_over_all_time']

client.to_pandas(f"""
  SELECT
    p.display_name AS project_display_name,
    m.display_name AS metric_display_name,
    km.sample_date,
    km.amount
  FROM key_metrics_by_project_v0 AS km
  JOIN metrics_v0 AS m ON m.metric_id = km.metric_id
  JOIN projects_v1 AS p ON p.project_id = km.project_id
  WHERE
    p.project_name IN ({stringify(MY_PROJECTS)})
    AND m.metric_name IN ({stringify(MY_METRICS)})
  ORDER BY p.display_name, m.display_name
""")
```

Get timeseries metrics for OSO:

```python
df_stars = client.to_pandas("""
  SELECT
    tm.metric_id,
    m.metric_name,
    m.display_name,
    tm.sample_date,
    tm.amount,
    tm.unit
  FROM timeseries_metrics_by_project_v0 AS tm
  JOIN metrics_v0 AS m ON m.metric_id = tm.metric_id
  JOIN projects_v1 AS p ON p.project_id = tm.project_id
  WHERE
    p.project_name = 'opensource-observer'
    AND m.metric_name = 'GITHUB_stars_daily'
  ORDER BY tm.sample_date
""")
```

Add a cumulative column:

```python
df_stars['cumulative_amount'] = df_stars['amount'].cumsum()
```

That's it! You're now ready to explore the OSO data lake using pyoso. For more examples, check out our other [tutorials](./index.md).
