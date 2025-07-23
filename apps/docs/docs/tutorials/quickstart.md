---
title: Pyoso Quickstart
description: Get started with pyoso and common query patterns for our most popular models
sidebar_position: 2
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

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

<Tabs>
<TabItem value="python" label="Python">

```python
client.to_pandas("SELECT * FROM models_v0 LIMIT 5")
```

</TabItem>
<TabItem value="python" label="Semantic Layer">

```python
query = semantic.select(
    "models_v0.*"
).limit(5)
```

</TabItem>
</Tabs>

Get the list of stable production models:

<Tabs>
<TabItem value="python" label="Python">

```python
client.to_pandas("SELECT * FROM models_v0 WHERE model_name LIKE '%_v1'")
```

</TabItem>
<TabItem value="python" label="Semantic Layer">

```python
query = oso.semantic.select(
    "models_v0",                 
).where(
    "models_v0.model_name LIKE '%_v1'"
)
```

</TabItem>
</Tabs>

Get the list of less stable models:

<Tabs>
<TabItem value="python" label="Python">

```python
client.to_pandas("SELECT * FROM models_v0 WHERE model_name LIKE '%_v0'")
```

</TabItem>
<TabItem value="python" label="Semantic Layer">

```python
query = oso.semantic.select(
    "models_v0",
).where(
    "models_v0.model_name LIKE '%_v0'"
)
```

</TabItem>
</Tabs>

## Query Popular Models

Get a list of projects:

<Tabs>
<TabItem value="python" label="Python">

```python
client.to_pandas("SELECT * FROM projects_v1 LIMIT 5")
```

</TabItem>
<TabItem value="python" label="Semantic Layer">

```python
query = oso.semantic.select(
    "projects_v1",
).limit(5)
```

</TabItem>
</Tabs>

Look up a specific project:

<Tabs>
<TabItem value="python" label="Python">

```python
client.to_pandas("SELECT * FROM projects_v1 WHERE project_name = 'opensource-observer'")
```

</TabItem>
<TabItem value="python" label="Semantic Layer">

```python
query = oso.semantic.select(
    "projects_v1",
).where(
    "projects_v1.project_name = 'opensource-observer'"
)
```

</TabItem>
</Tabs>

Get all artifacts owned by a project:

<Tabs>
<TabItem value="python" label="Python">

```python
client.to_pandas("SELECT * FROM artifacts_by_project_v1 WHERE project_name = 'opensource-observer'")
```

</TabItem>
<TabItem value="python" label="Semantic Layer">

```python
query = oso.semantic.select(
    "artifacts_by_project_v1",
).where(
    "artifacts_by_project_v1.project_name = 'opensource-observer'"
)
```

</TabItem>
</Tabs>

Get available key metrics for OSO:

<Tabs>
<TabItem value="python" label="Python">

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

</TabItem>
<TabItem value="python" label="Semantic Layer">

```python
query = oso.semantic.select(
    "key_metrics_by_project_v0.metric_id",
    "metrics_v0.metric_name",
    "metrics_v0.display_name",
    "key_metrics_by_project_v0.sample_date",
    "key_metrics_by_project_v0.amount",
    "key_metrics_by_project_v0.unit",
).join(
    "metrics_v0", 
    on="key_metrics_by_project_v0.metric_id = metrics_v0.metric_id"
).where(
    "key_metrics_by_project_v0.project_id = 'UuWbpo5bpL5QsYvlukUWNm2uE8HFjxQxzCM0e+HMZfk='"
)
```

</TabItem>
</Tabs>

Get a set of key metrics for a few projects:

<Tabs>
<TabItem value="python" label="Python">

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

</TabItem>
<TabItem value="python" label="Semantic Layer">

```python
MY_PROJECTS = ['opensource-observer', 'huggingface', 'wevm']
MY_METRICS = ['GITHUB_stars_over_all_time', 'GITHUB_forks_over_all_time']

oso = Client()  # ensure OSO_API_KEY is set

query = (
    oso.semantic.select(
        "projects_v1.display_name",
        "metrics_v0.display_name",
        "key_metrics_by_project_v0.sample_date",
        "key_metrics_by_project_v0.amount",
    )
    .join(
        "metrics_v0",
        on="metrics_v0.metric_id = key_metrics_by_project_v0.metric_id"
    )
    .join(
        "projects_v1",
        on="projects_v1.project_id = key_metrics_by_project_v0.project_id"
    )
    .where(
        f"projects_v1.project_name IN ({', '.join(repr(p) for p in MY_PROJECTS)})",
        f"metrics_v0.metric_name IN ({', '.join(repr(m) for m in MY_METRICS)})",
    )
    .order_by("projects_v1.display_name", "metrics_v0.display_name")
)
```

</TabItem>
</Tabs>

Get timeseries metrics for OSO:

<Tabs>
<TabItem value="python" label="Python">

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

</TabItem>
<TabItem value="python" label="Semantic Layer">

```python
query = (
    oso.semantic.select(
        "timeseries_metrics_by_project_v0.metric_id",
        "metrics_v0.metric_name",
        "metrics_v0.display_name",
        "timeseries_metrics_by_project_v0.sample_date",
        "timeseries_metrics_by_project_v0.amount",
        "timeseries_metrics_by_project_v0.unit",
    )
    .join(
        "metrics_v0",
        on="metrics_v0.metric_id = timeseries_metrics_by_project_v0.metric_id"
    )
    .join(
        "projects_v1",
        on="projects_v1.project_id = timeseries_metrics_by_project_v0.project_id"
    )
    .where(
        "projects_v1.project_name = 'opensource-observer'",
        "metrics_v0.metric_name = 'GITHUB_stars_daily'"
    )
    .order_by("timeseries_metrics_by_project_v0.sample_date")
)
```

</TabItem>
</Tabs>

Add a cumulative column:

```python
df_stars['cumulative_amount'] = df_stars['amount'].cumsum()
```

That's it! You're now ready to explore the OSO data lake using pyoso. For more examples, check out our other [tutorials](./index.md).
