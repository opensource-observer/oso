---
title: Create a Network Graph
sidebar_position: 5
---

Create a developer graph for related groups of projects. New to OSO? Check out our [Getting Started guide](../get-started/index.md) to set up your BigQuery or API access.

This tutorial combines various datasets to create a developer contribution graph. The graph highlights developers who have contributed to relevant repositories with onchain activity and shows their interactions with other (mostly off-chain) repositories. The analysis objective is to identify core developers contributing to specific projects and track their interactions with other repositories.

Here's a visualization of the final result:

![Network Graph](network-graph.png)

## BigQuery

If you haven't already, then the first step is to subscribe to OSO public datasets in BigQuery. You can do this by clicking the "Subscribe" button on our [Datasets page](../integrate/datasets/#oso-production-data-pipeline).

The following queries should work if you copy-paste them into your [BigQuery console](https://console.cloud.google.com/bigquery).

### Identify relevant projects

We'll start by identifying projects with significant onchain activity on chains we're interested in. This is done by querying the `oso_production.onchain_metrics_by_project_v1` table to select projects with:

- A minimum number of transactions (`txns > 1000`)
- A minimum number of users (`users > 420`)
- Activity on specific chains (`OPTIMISM`, `BASE`, `MODE`)

```sql
with relevant_projects as (
  select
    project_id,
    project_name,
    sum(gas_fees_sum_6_months) as gas_fees,
    sum(transaction_count_6_months) as txns,
    sum(address_count_90_days) as users
  from `oso_production.onchain_metrics_by_project_v1`
  where event_source in ('OPTIMISM', 'BASE', 'MODE')
  group by 1, 2
  having txns > 1000 and users > 420
)
```

### Fetch relevant repositories

Next, we identify repositories related to these projects by joining with the `oso_production.repositories_v0` table. We filter for repositories using specific programming languages (`TypeScript`, `Solidity`, `Rust`).

```sql
relevant_repos as (
  select rm.artifact_id, p.project_name, p.project_id
  from `oso_production.repositories_v0` rm
  join relevant_projects p on rm.project_id = p.project_id
  where rm.language in ('TypeScript', 'Solidity', 'Rust')
)
```

### Identify core developers

We then identify core developers who have made significant contributions to these repositories. This involves querying the `oso_production.timeseries_events_by_artifact_v0` table for developers who:

- Have committed code (`event_type = 'COMMIT_CODE'`)
- Are not bots
- Have contributed over multiple months and with a minimum amount

```sql
core_devs as (
  select
    e.from_artifact_id as developer_id,
    u.display_name as developer_name,
    e.to_artifact_id as repo_id
  from `oso_production.timeseries_events_by_artifact_v0` e
  join `oso_production.users_v1` u
  on e.from_artifact_id = u.user_id
  where e.to_artifact_id in (select artifact_id from relevant_repos)
    and e.event_type = 'COMMIT_CODE'
    and u.display_name not like '%[bot]%'
  group by 1,2,3
  having count(distinct date_trunc(time, month)) >= 3
    and sum(amount) >= 20
)
```

### Filter repositories with releases

We focus on target repositories that have published releases by querying the `oso_production.int_events__github` table for `RELEASE_PUBLISHED` events.

```sql
repos_with_releases as (
  select distinct to_artifact_id
  from `oso_production.timeseries_events_by_artifact_v0`
  where event_type = 'RELEASE_PUBLISHED'
)
```

### Track developer interactions

Finally, we track interactions of core developers with other repositories. We join the datasets to gather information about:

- Source project metrics (gas fees, transactions, users)
- Target project interactions (days, amount, types)

```sql
dev_other_repos as (
  select
    cd.developer_id,
    cd.developer_name,
    rr.project_name as source_project,
    rp.gas_fees as source_project_gas_fees,
    rp.txns as source_project_txns,
    rp.users as source_project_users,
    target_rm.artifact_namespace,
    target_rm.artifact_name,
    target_p.project_name as target_project_name,
    count(distinct date_trunc(e.time, day)) as target_project_interaction_days_from_dev,
    sum(e.amount) as target_project_interaction_amount_from_dev,
    count(distinct e.event_type) as target_project_interaction_types_distinct
  from core_devs cd
  join relevant_repos rr on cd.repo_id = rr.artifact_id
  join relevant_projects rp on rr.project_id = rp.project_id
  join `oso_production.timeseries_events_by_artifact_v0` e on cd.developer_id = e.from_artifact_id
  left join `oso_production.repositories_v0` target_rm on e.to_artifact_id = target_rm.artifact_id
  left join `oso_production.projects_v1` target_p on target_rm.project_id = target_p.project_id
    where e.to_artifact_id not in (select artifact_id from relevant_repos)
    and e.to_artifact_id in (select to_artifact_id from repos_with_releases)
    and e.time >= '2023-01-01'
  group by 1,2,3,4,5,6,7,8,9
  having count(distinct date_trunc(e.time, day)) >= 1
)
```

### Select final results

The final selection filters out interactions where the source and target projects are the same and orders the results by interaction days.

```sql
select * from dev_other_repos
where source_project != target_project_name
order by target_project_interaction_days_from_dev desc
```

### Run the full query

Here's the full query for the network graph:

```sql
-- Step 1: Identify relevant projects with sufficient activity
with relevant_projects as (
  select
    project_id,
    project_name,
    sum(gas_fees_sum_6_months) as gas_fees,
    sum(transaction_count_6_months) as txns,
    sum(address_count_90_days) as users
  from `oso_production.onchain_metrics_by_project_v1`
  where event_source in ('OPTIMISM', 'BASE', 'MODE')
  group by project_id, project_name
  having txns > 1000 and users > 420
),

-- Step 2: Fetch repositories related to the relevant projects
relevant_repos as (
  select
    rm.artifact_id,
    p.project_name,
    p.project_id
  from `oso_production.repositories_v0` rm
  join relevant_projects p on rm.project_id = p.project_id
  where rm.language in ('TypeScript', 'Solidity', 'Rust')
),

-- Step 3: Identify core developers with significant contributions
core_devs as (
  select
    e.from_artifact_id as developer_id,
    u.display_name as developer_name,
    e.to_artifact_id as repo_id
  from `oso_production.timeseries_events_by_artifact_v0` e
  join `oso_production.users_v1` u
  on e.from_artifact_id = u.user_id
  where e.to_artifact_id in (select artifact_id from relevant_repos)
    and e.event_type = 'COMMIT_CODE'
    and u.display_name not like '%[bot]%'
  group by 1,2,3
  having count(distinct date_trunc(time, month)) >= 3
    and sum(amount) >= 20
),

-- Step 4: Identify repositories that published releases
repos_with_releases as (
  select distinct to_artifact_id
  from `oso_production.timeseries_events_by_artifact_v0`
  where event_type = 'RELEASE_PUBLISHED'
),

-- Step 5: Fetch interactions of core developers in other repositories
dev_other_repos as (
  select
    cd.developer_id,
    cd.developer_name,
    rr.project_name as source_project,
    rp.gas_fees as source_project_gas_fees,
    rp.txns as source_project_txns,
    rp.users as source_project_users,
    target_rm.artifact_namespace,
    target_rm.artifact_name,
    target_p.project_name as target_project_name,
    count(distinct date_trunc(e.time, day)) as target_project_interaction_days_from_dev,
    sum(e.amount) as target_project_interaction_amount_from_dev,
    count(distinct e.event_type) as target_project_interaction_types_distinct
  from core_devs cd
  join relevant_repos rr on cd.repo_id = rr.artifact_id
  join relevant_projects rp on rr.project_id = rp.project_id
  join `oso_production.timeseries_events_by_artifact_v0` e on cd.developer_id = e.from_artifact_id
  left join `oso_production.repositories_v0` target_rm on e.to_artifact_id = target_rm.artifact_id
  left join `oso_production.projects_v1` target_p on target_rm.project_id = target_p.project_id
  where e.to_artifact_id not in (select artifact_id from relevant_repos)
    and e.to_artifact_id in (select to_artifact_id from repos_with_releases)
    and e.time >= '2023-01-01'
  group by 1,2,3,4,5,6,7,8,9
  having count(distinct date_trunc(e.time, day)) >= 1
)

-- Step 6: Select final results
select * from dev_other_repos
where source_project != target_project_name
order by target_project_interaction_days_from_dev desc
```

## Python

See our guide on [writing Python notebooks](../guides/notebooks/index.mdx) for more information on how to connect to BigQuery and query data. Our [Insights Repo](https://github.com/opensource-observer/insights) is full of examples too.

### Connect to BigQuery

You can use the following to connect to BigQuery:

```python
from google.cloud import bigquery
import pandas as pd
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = # PATH TO YOUR CREDENTIALS JSON
GCP_PROJECT = # YOUR GCP PROJECT NAME

client = bigquery.Client(GCP_PROJECT)
```

### Execute the full query

To run this query in Python, you can use the following:

```python
query = """
-- Step 1: Identify relevant projects with sufficient activity
with relevant_projects as (
  select
    project_id,
    project_name,
    sum(gas_fees_sum_6_months) as gas_fees,
    sum(transaction_count_6_months) as txns,
    sum(address_count_90_days) as users
  from `oso_production.onchain_metrics_by_project_v1`
  where event_source in ('OPTIMISM', 'BASE', 'MODE')
  group by project_id, project_name
  having txns > 1000 and users > 420
),

-- Step 2: Fetch repositories related to the relevant projects
relevant_repos as (
  select
    rm.artifact_id,
    p.project_name,
    p.project_id
  from `oso_production.repositories_v0` rm
  join relevant_projects p on rm.project_id = p.project_id
  where rm.language in ('TypeScript', 'Solidity', 'Rust')
),

-- Step 3: Identify core developers with significant contributions
core_devs as (
  select
    e.from_artifact_id as developer_id,
    u.display_name as developer_name,
    e.to_artifact_id as repo_id
  from `oso_production.timeseries_events_by_artifact_v0` e
  join `oso_production.users_v1` u
  on e.from_artifact_id = u.user_id
  where e.to_artifact_id in (select artifact_id from relevant_repos)
    and e.event_type = 'COMMIT_CODE'
    and u.display_name not like '%[bot]%'
  group by 1,2,3
  having count(distinct date_trunc(time, month)) >= 3
    and sum(amount) >= 20
),

-- Step 4: Identify repositories that published releases
repos_with_releases as (
  select distinct to_artifact_id
  from `oso_production.timeseries_events_by_artifact_v0`
  where event_type = 'RELEASE_PUBLISHED'
),

-- Step 5: Fetch interactions of core developers in other repositories
dev_other_repos as (
  select
    cd.developer_id,
    cd.developer_name,
    rr.project_name as source_project,
    rp.gas_fees as source_project_gas_fees,
    rp.txns as source_project_txns,
    rp.users as source_project_users,
    target_rm.artifact_namespace,
    target_rm.artifact_name,
    target_p.project_name as target_project_name,
    count(distinct date_trunc(e.time, day)) as target_project_interaction_days_from_dev,
    sum(e.amount) as target_project_interaction_amount_from_dev,
    count(distinct e.event_type) as target_project_interaction_types_distinct
  from core_devs cd
  join relevant_repos rr on cd.repo_id = rr.artifact_id
  join relevant_projects rp on rr.project_id = rp.project_id
  join `oso_production.timeseries_events_by_artifact_v0` e on cd.developer_id = e.from_artifact_id
  left join `oso_production.repositories_v0` target_rm on e.to_artifact_id = target_rm.artifact_id
  left join `oso_production.projects_v1` target_p on target_rm.project_id = target_p.project_id
  where e.to_artifact_id not in (select artifact_id from relevant_repos)
    and e.to_artifact_id in (select to_artifact_id from repos_with_releases)
    and e.time >= '2023-01-01'
  group by 1,2,3,4,5,6,7,8,9
  having count(distinct date_trunc(e.time, day)) >= 1
)

-- Step 6: Select final results
select *
from dev_other_repos
where source_project != target_project_name
order by target_project_interaction_days_from_dev desc

"""

result = client.query(query)
df = result.to_dataframe()
df.head()
```

### Visualize the results

Now that we have the data, we can visualize it using a network graph. Here's an example of how to do this using the `networkx` library:

```python
import networkx as nx
import matplotlib.pyplot as plt

G = nx.Graph()
for (source, target), weight in (
    df.groupby(['source_project', 'target_project_name'])
    ['developer_id']
    .nunique()
    .items()
):
    G.add_nodes_from([source, target])
    G.add_edge(source, target, weight=weight)

degrees = dict(G.degree)
scaled_node_size = [degrees[k] ** 1.8 for k in degrees]

pos = nx.spring_layout(G, scale=2, k=1, seed=42)

fig, ax = plt.subplots(figsize=(20, 20), dpi=300)
nx.draw(
    G,
    pos,
    nodelist=degrees,
    node_size=scaled_node_size,
    node_color="red",
    edge_color="gray",
    width=0.1,
    with_labels=True,
    font_size=10,
    font_weight="bold",
    alpha=0.7,
    ax=ax
)

ax.set_title("Projects with Common Contributors", fontsize=18, fontweight="bold", pad=20)
ax.axis("off")

plt.tight_layout()
plt.show()
```
