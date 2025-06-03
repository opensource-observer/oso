---
title: Create a Network Graph
sidebar_position: 6
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

Create a developer graph for related groups of projects.
New to OSO? Check out our [Getting Started guide](../get-started/index.md)
to set up your API access.

This tutorial combines various datasets to create a developer contribution graph. The graph highlights developers who have contributed to relevant repositories with onchain activity and shows their interactions with other (mostly off-chain) repositories. The analysis objective is to identify core developers contributing to specific projects and track their interactions with other repositories.

Here's a visualization of the final result:

![Network Graph](network-graph.png)

## Getting Started

Before running any analysis, you'll need to set up your environment:

<Tabs>
<TabItem value="python" label="Python">

Start your Python notebook with the following:

```python
import os
import pandas as pd
from pyoso import Client

OSO_API_KEY = os.environ['OSO_API_KEY']
client = Client(api_key=OSO_API_KEY)
```

For more details on setting up Python notebooks, see our guide on [writing Python notebooks](../guides/notebooks/index.mdx).

</TabItem>
<TabItem value="graphql" label="GraphQL">

The following queries should work if you copy-paste them into our [GraphQL sandbox](https://www.opensource.observer/graphql). For more information on how to use the GraphQL API, check out our [GraphQL guide](../integrate/api.md).

</TabItem>
</Tabs>

## Building a Network Graph

### Identify relevant projects

We'll start by identifying projects with significant onchain activity on chains we're interested in. This is done by querying the `onchain_metrics_by_project_v1` table to select projects with:

- A minimum number of transactions (`txns > 1000`)
- A minimum number of users (`users > 420`)
- Activity on specific chains (`OPTIMISM`, `BASE`, `MODE`)

<Tabs>
<TabItem value="python" label="Python">

```python
query = """
WITH relevant_projects AS (
  SELECT
    project_id,
    project_name,
    SUM(gas_fees_sum_6_months) AS gas_fees,
    SUM(transaction_count_6_months) AS txns,
    SUM(address_count_90_days) AS users
  FROM onchain_metrics_by_project_v1
  WHERE event_source IN ('OPTIMISM', 'BASE', 'MODE')
  GROUP BY 1, 2
  HAVING txns > 1000 AND users > 420
)
SELECT * FROM relevant_projects
"""
relevant_projects_df = client.to_pandas(query)
```

</TabItem>
<TabItem value="graphql" label="GraphQL">

```graphql
query RelevantProjects {
  oso_onchainMetricsByProjectV1(
    where: { eventSource: { _in: ["OPTIMISM", "BASE", "MODE"] } }
  ) {
    projectId
    projectName
    gasFeesSum6Months
    transactionCount6Months
    addressCount90Days
    eventSource
  }
}
```

Note: With GraphQL, you would need to perform the aggregation and filtering client-side after fetching the data.

</TabItem>
</Tabs>

### Fetch relevant repositories

Next, we identify repositories related to these projects by joining with the `repositories_v0` table. We filter for repositories using specific programming languages (`TypeScript`, `Solidity`, `Rust`).

<Tabs>
<TabItem value="python" label="Python">

```python
query = """
WITH relevant_projects AS (
  SELECT
    project_id,
    project_name,
    SUM(gas_fees_sum_6_months) AS gas_fees,
    SUM(transaction_count_6_months) AS txns,
    SUM(address_count_90_days) AS users
  FROM onchain_metrics_by_project_v1
  WHERE event_source IN ('OPTIMISM', 'BASE', 'MODE')
  GROUP BY 1, 2
  HAVING txns > 1000 AND users > 420
)
SELECT rm.artifact_id, p.project_name, p.project_id
FROM repositories_v0 rm
JOIN relevant_projects p ON rm.project_id = p.project_id
WHERE rm.language IN ('TypeScript', 'Solidity', 'Rust')
"""
relevant_repos_df = client.to_pandas(query)
```

</TabItem>
<TabItem value="graphql" label="GraphQL">

```graphql
query RelevantRepositories {
  # First get relevant projects (would need client-side filtering)
  projects: oso_onchainMetricsByProjectV1(
    where: { eventSource: { _in: ["OPTIMISM", "BASE", "MODE"] } }
  ) {
    projectId
    projectName
    transactionCount6Months
    addressCount90Days
  }

  # Then get repositories for those projects
  repositories: oso_repositoriesV0(
    where: { language: { _in: ["TypeScript", "Solidity", "Rust"] } }
  ) {
    artifactId
    projectId
    language
  }
}
```

Note: With GraphQL, you would need to join these datasets client-side after fetching the data.

</TabItem>
</Tabs>

### Identify core developers

We then identify core developers who have made significant contributions to these repositories. This involves querying the `timeseries_events_by_artifact_v0` table for developers who:

- Have committed code (`event_type = 'COMMIT_CODE'`)
- Are not bots
- Have contributed over multiple months and with a minimum amount

<Tabs>
<TabItem value="python" label="Python">

```python
query = """
WITH relevant_projects AS (
  SELECT
    project_id,
    project_name,
    SUM(gas_fees_sum_6_months) AS gas_fees,
    SUM(transaction_count_6_months) AS txns,
    SUM(address_count_90_days) AS users
  FROM onchain_metrics_by_project_v1
  WHERE event_source IN ('OPTIMISM', 'BASE', 'MODE')
  GROUP BY 1, 2
  HAVING txns > 1000 AND users > 420
),
relevant_repos AS (
  SELECT rm.artifact_id, p.project_name, p.project_id
  FROM repositories_v0 rm
  JOIN relevant_projects p ON rm.project_id = p.project_id
  WHERE rm.language IN ('TypeScript', 'Solidity', 'Rust')
)
SELECT
  e.from_artifact_id AS developer_id,
  u.display_name AS developer_name,
  e.to_artifact_id AS repo_id
FROM timeseries_events_by_artifact_v0 e
JOIN users_v1 u
  ON e.from_artifact_id = u.user_id
WHERE e.to_artifact_id IN (SELECT artifact_id FROM relevant_repos)
  AND e.event_type = 'COMMIT_CODE'
  AND u.display_name NOT LIKE '%[bot]%'
GROUP BY 1,2,3
HAVING COUNT(DISTINCT DATE_TRUNC(time, MONTH)) >= 3
  AND SUM(amount) >= 20
"""
core_devs_df = client.to_pandas(query)
```

</TabItem>
<TabItem value="graphql" label="GraphQL">

```graphql
query CoreDevelopers {
  # This complex query requires multiple steps and client-side processing
  # First get events for repositories of interest
  events: oso_timeseriesEventsByArtifactV0(
    where: { eventType: { _eq: "COMMIT_CODE" } }
  ) {
    fromArtifactId
    toArtifactId
    time
    amount
  }

  # Get user information
  users: oso_usersV1 {
    userId
    displayName
  }
}
```

Note: With GraphQL, you would need to perform the filtering, joining, and aggregation client-side after fetching the data.

</TabItem>
</Tabs>

### Filter repositories with releases

We focus on target repositories that have published releases by querying for `RELEASE_PUBLISHED` events.

<Tabs>
<TabItem value="python" label="Python">

```python
query = """
SELECT DISTINCT to_artifact_id
FROM timeseries_events_by_artifact_v0
WHERE event_type = 'RELEASE_PUBLISHED'
"""
repos_with_releases_df = client.to_pandas(query)
```

</TabItem>
<TabItem value="graphql" label="GraphQL">

```graphql
query RepositoriesWithReleases {
  oso_timeseriesEventsByArtifactV0(
    where: { eventType: { _eq: "RELEASE_PUBLISHED" } }
    distinct_on: [toArtifactId]
  ) {
    toArtifactId
  }
}
```

</TabItem>
</Tabs>

### Track developer interactions

Finally, we track interactions of core developers with other repositories. We join the datasets to gather information about:

- Source project metrics (gas fees, transactions, users)
- Target project interactions (days, amount, types)

<Tabs>
<TabItem value="python" label="Python">

```python
query = """
WITH relevant_projects AS (
  SELECT
    project_id,
    project_name,
    SUM(gas_fees_sum_6_months) AS gas_fees,
    SUM(transaction_count_6_months) AS txns,
    SUM(address_count_90_days) AS users
  FROM onchain_metrics_by_project_v1
  WHERE event_source IN ('OPTIMISM', 'BASE', 'MODE')
  GROUP BY 1, 2
  HAVING txns > 1000 AND users > 420
),
relevant_repos AS (
  SELECT rm.artifact_id, p.project_name, p.project_id
  FROM repositories_v0 rm
  JOIN relevant_projects p ON rm.project_id = p.project_id
  WHERE rm.language IN ('TypeScript', 'Solidity', 'Rust')
),
core_devs AS (
  SELECT
    e.from_artifact_id AS developer_id,
    u.display_name AS developer_name,
    e.to_artifact_id AS repo_id
  FROM timeseries_events_by_artifact_v0 e
  JOIN users_v1 u
    ON e.from_artifact_id = u.user_id
  WHERE e.to_artifact_id IN (SELECT artifact_id FROM relevant_repos)
    AND e.event_type = 'COMMIT_CODE'
    AND u.display_name NOT LIKE '%[bot]%'
  GROUP BY 1,2,3
  HAVING COUNT(DISTINCT DATE_TRUNC(time, MONTH)) >= 3
    AND SUM(amount) >= 20
),
repos_with_releases AS (
  SELECT DISTINCT to_artifact_id
  FROM timeseries_events_by_artifact_v0
  WHERE event_type = 'RELEASE_PUBLISHED'
)
SELECT
  cd.developer_id,
  cd.developer_name,
  rr.project_name AS source_project,
  rp.gas_fees AS source_project_gas_fees,
  rp.txns AS source_project_txns,
  rp.users AS source_project_users,
  target_rm.artifact_namespace,
  target_rm.artifact_name,
  target_p.project_name AS target_project_name,
  COUNT(DISTINCT DATE_TRUNC(e.time, DAY)) AS target_project_interaction_days_from_dev,
  SUM(e.amount) AS target_project_interaction_amount_from_dev,
  COUNT(DISTINCT e.event_type) AS target_project_interaction_types_distinct
FROM core_devs cd
JOIN relevant_repos rr ON cd.repo_id = rr.artifact_id
JOIN relevant_projects rp ON rr.project_id = rp.project_id
JOIN timeseries_events_by_artifact_v0 e ON cd.developer_id = e.from_artifact_id
LEFT JOIN repositories_v0 target_rm ON e.to_artifact_id = target_rm.artifact_id
LEFT JOIN projects_v1 target_p ON target_rm.project_id = target_p.project_id
WHERE e.to_artifact_id NOT IN (SELECT artifact_id FROM relevant_repos)
  AND e.to_artifact_id IN (SELECT to_artifact_id FROM repos_with_releases)
  AND e.time >= '2023-01-01'
GROUP BY 1,2,3,4,5,6,7,8,9
HAVING COUNT(DISTINCT DATE_TRUNC(e.time, DAY)) >= 1
"""
dev_other_repos_df = client.to_pandas(query)
```

</TabItem>
<TabItem value="graphql" label="GraphQL">

```graphql
query DeveloperInteractions {
  # This complex query requires multiple steps and client-side processing
  # The Python approach is recommended for this type of analysis

  # You would need to fetch data from multiple sources and join them client-side
  # This is a simplified example showing the general approach
  events: oso_timeseriesEventsByArtifactV0(
    where: { time: { _gte: "2023-01-01" } }
  ) {
    fromArtifactId
    toArtifactId
    time
    eventType
    amount
  }

  repositories: oso_repositoriesV0 {
    artifactId
    artifactNamespace
    artifactName
    projectId
  }

  projects: oso_projectsV1 {
    projectId
    projectName
  }
}
```

Note: For complex analyses like this, the Python approach is more efficient as it handles the joins and calculations server-side.

</TabItem>
</Tabs>

### Select final results

The final selection filters out interactions where the source and target projects are the same and orders the results by interaction days.

<Tabs>
<TabItem value="python" label="Python">

```python
query = """
WITH relevant_projects AS (
  SELECT
    project_id,
    project_name,
    SUM(gas_fees_sum_6_months) AS gas_fees,
    SUM(transaction_count_6_months) AS txns,
    SUM(address_count_90_days) AS users
  FROM onchain_metrics_by_project_v1
  WHERE event_source IN ('OPTIMISM', 'BASE', 'MODE')
  GROUP BY 1, 2
  HAVING txns > 1000 AND users > 420
),
relevant_repos AS (
  SELECT rm.artifact_id, p.project_name, p.project_id
  FROM repositories_v0 rm
  JOIN relevant_projects p ON rm.project_id = p.project_id
  WHERE rm.language IN ('TypeScript', 'Solidity', 'Rust')
),
core_devs AS (
  SELECT
    e.from_artifact_id AS developer_id,
    u.display_name AS developer_name,
    e.to_artifact_id AS repo_id
  FROM timeseries_events_by_artifact_v0 e
  JOIN users_v1 u
    ON e.from_artifact_id = u.user_id
  WHERE e.to_artifact_id IN (SELECT artifact_id FROM relevant_repos)
    AND e.event_type = 'COMMIT_CODE'
    AND u.display_name NOT LIKE '%[bot]%'
  GROUP BY 1,2,3
  HAVING COUNT(DISTINCT DATE_TRUNC(time, MONTH)) >= 3
    AND SUM(amount) >= 20
),
repos_with_releases AS (
  SELECT DISTINCT to_artifact_id
  FROM timeseries_events_by_artifact_v0
  WHERE event_type = 'RELEASE_PUBLISHED'
),
dev_other_repos AS (
  SELECT
    cd.developer_id,
    cd.developer_name,
    rr.project_name AS source_project,
    rp.gas_fees AS source_project_gas_fees,
    rp.txns AS source_project_txns,
    rp.users AS source_project_users,
    target_rm.artifact_namespace,
    target_rm.artifact_name,
    target_p.project_name AS target_project_name,
    COUNT(DISTINCT DATE_TRUNC(e.time, DAY)) AS target_project_interaction_days_from_dev,
    SUM(e.amount) AS target_project_interaction_amount_from_dev,
    COUNT(DISTINCT e.event_type) AS target_project_interaction_types_distinct
  FROM core_devs cd
  JOIN relevant_repos rr ON cd.repo_id = rr.artifact_id
  JOIN relevant_projects rp ON rr.project_id = rp.project_id
  JOIN timeseries_events_by_artifact_v0 e ON cd.developer_id = e.from_artifact_id
  LEFT JOIN repositories_v0 target_rm ON e.to_artifact_id = target_rm.artifact_id
  LEFT JOIN projects_v1 target_p ON target_rm.project_id = target_p.project_id
  WHERE e.to_artifact_id NOT IN (SELECT artifact_id FROM relevant_repos)
    AND e.to_artifact_id IN (SELECT to_artifact_id FROM repos_with_releases)
    AND e.time >= '2023-01-01'
  GROUP BY 1,2,3,4,5,6,7,8,9
  HAVING COUNT(DISTINCT DATE_TRUNC(e.time, DAY)) >= 1
)
SELECT * FROM dev_other_repos
WHERE source_project != target_project_name
ORDER BY target_project_interaction_days_from_dev DESC
"""
final_results_df = client.to_pandas(query)
```

</TabItem>
<TabItem value="graphql" label="GraphQL">

```graphql
# For this final step, you would process the data client-side
# after fetching it with the previous GraphQL queries
```

</TabItem>
</Tabs>

### Run the full query

Here's the full query for the network graph:

<Tabs>
<TabItem value="python" label="Python">

```python
query = """
-- Step 1: Identify relevant projects with sufficient activity
WITH relevant_projects AS (
  SELECT
    project_id,
    project_name,
    SUM(gas_fees_sum_6_months) AS gas_fees,
    SUM(transaction_count_6_months) AS txns,
    SUM(address_count_90_days) AS users
  FROM onchain_metrics_by_project_v1
  WHERE event_source IN ('OPTIMISM', 'BASE', 'MODE')
  GROUP BY project_id, project_name
  HAVING txns > 1000 AND users > 420
),

-- Step 2: Fetch repositories related to the relevant projects
relevant_repos AS (
  SELECT
    rm.artifact_id,
    p.project_name,
    p.project_id
  FROM repositories_v0 rm
  JOIN relevant_projects p ON rm.project_id = p.project_id
  WHERE rm.language IN ('TypeScript', 'Solidity', 'Rust')
),

-- Step 3: Identify core developers with significant contributions
core_devs AS (
  SELECT
    e.from_artifact_id AS developer_id,
    u.display_name AS developer_name,
    e.to_artifact_id AS repo_id
  FROM timeseries_events_by_artifact_v0 e
  JOIN users_v1 u
  ON e.from_artifact_id = u.user_id
  WHERE e.to_artifact_id IN (SELECT artifact_id FROM relevant_repos)
    AND e.event_type = 'COMMIT_CODE'
    AND u.display_name NOT LIKE '%[bot]%'
  GROUP BY 1,2,3
  HAVING COUNT(DISTINCT DATE_TRUNC(time, MONTH)) >= 3
    AND SUM(amount) >= 20
),

-- Step 4: Identify repositories that published releases
repos_with_releases AS (
  SELECT DISTINCT to_artifact_id
  FROM timeseries_events_by_artifact_v0
  WHERE event_type = 'RELEASE_PUBLISHED'
),

-- Step 5: Fetch interactions of core developers in other repositories
dev_other_repos AS (
  SELECT
    cd.developer_id,
    cd.developer_name,
    rr.project_name AS source_project,
    rp.gas_fees AS source_project_gas_fees,
    rp.txns AS source_project_txns,
    rp.users AS source_project_users,
    target_rm.artifact_namespace,
    target_rm.artifact_name,
    target_p.project_name AS target_project_name,
    COUNT(DISTINCT DATE_TRUNC(e.time, DAY)) AS target_project_interaction_days_from_dev,
    SUM(e.amount) AS target_project_interaction_amount_from_dev,
    COUNT(DISTINCT e.event_type) AS target_project_interaction_types_distinct
  FROM core_devs cd
  JOIN relevant_repos rr ON cd.repo_id = rr.artifact_id
  JOIN relevant_projects rp ON rr.project_id = rp.project_id
  JOIN timeseries_events_by_artifact_v0 e ON cd.developer_id = e.from_artifact_id
  LEFT JOIN repositories_v0 target_rm ON e.to_artifact_id = target_rm.artifact_id
  LEFT JOIN projects_v1 target_p ON target_rm.project_id = target_p.project_id
  WHERE e.to_artifact_id NOT IN (SELECT artifact_id FROM relevant_repos)
    AND e.to_artifact_id IN (SELECT to_artifact_id FROM repos_with_releases)
    AND e.time >= '2023-01-01'
  GROUP BY 1,2,3,4,5,6,7,8,9
  HAVING COUNT(DISTINCT DATE_TRUNC(e.time, DAY)) >= 1
)

-- Step 6: Select final results
SELECT * FROM dev_other_repos
WHERE source_project != target_project_name
ORDER BY target_project_interaction_days_from_dev DESC
"""
result = client.to_pandas(query)
```

</TabItem>
<TabItem value="graphql" label="GraphQL">

```graphql
# For complex analyses like this network graph, the Python approach with pyoso
# is recommended as it handles the complex joins and aggregations more efficiently
```

</TabItem>
</Tabs>

## Visualize the Results

Now that we have the data, we can visualize it using a network graph:

```python
import networkx as nx
import matplotlib.pyplot as plt

# Create a graph from the results
G = nx.Graph()
for (source, target), weight in (
    result.groupby(['source_project', 'target_project_name'])
    ['developer_id']
    .nunique()
    .items()
):
    G.add_nodes_from([source, target])
    G.add_edge(source, target, weight=weight)

# Scale node sizes based on their degree
degrees = dict(G.degree)
scaled_node_size = [degrees[k] ** 1.8 for k in degrees]

# Create a spring layout
pos = nx.spring_layout(G, scale=2, k=1, seed=42)

# Draw the graph
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

This visualization shows the connections between projects based on shared contributors. The size of each node represents how central it is in the network (how many connections it has). This can help identify key projects that serve as bridges between different parts of the ecosystem.

For more examples of network analysis, check out our [Insights Repo](https://github.com/opensource-observer/insights).
