---
title: Event Types
sidebar_position: 3
---

:::info
An **event** is a record of a transaction or other activity involving an artifact, or a snapshot of cumulative events at a given point in time. Events are used to track the history of an artifact.
:::

## Overview

---

Every event is associated with an artifact that belongs to a single project. For example, a GitHub commit event is an event `from` a GitHub user artifact `to` a GitHub repo artifact owned by a single project. Similarly, a blockchain transaction event would be an event `from` a blockchain address artifact `to` another blockchain address artifact owned by a single project.

The `to` and `from` relationships between artifacts in an event are critical to OSO's ability to understand the impact of a project's activities and situate it in the context of overall network/ecosystem activity.

## Event Sources

---

All sources of event data are associated with a unique `event_source`. We are adding new event sources all the time. The `event_source` is the same as the `artifact_source` for the artifacts the `to` and `from` artifacts in the event.

## Event Sources and Types

---

OSO tracks events from multiple sources, each with its own set of event types. Below is a list of key event sources and their associated event types.

### GitHub Events (GITHUB)

GitHub events track activities related to code repositories, including commits, issues, pull requests, and more.

#### Code Events

- **COMMIT_CODE**: A commit made to a code repository
- **FORKED**: A repository being forked by a user
- **RELEASE_PUBLISHED**: Publication of a new release version
- **STARRED**: A repository being starred by a user

#### Issue Events

- **ISSUE_OPENED**: Opening of a new issue
- **ISSUE_CLOSED**: Closing of an issue
- **ISSUE_REOPENED**: Reopening of a previously closed issue
- **ISSUE_COMMENT**: A comment made on an issue

#### Pull Request Events

- **PULL_REQUEST_OPENED**: Opening of a new pull request
- **PULL_REQUEST_CLOSED**: Closing of a pull request
- **PULL_REQUEST_MERGED**: Merging of a pull request into the main branch
- **PULL_REQUEST_REOPENED**: Reopening of a previously closed pull request
- **PULL_REQUEST_REVIEW_COMMENT**: A comment made during pull request review

#### Derived Metrics

- **Commit Frequency**: Number of commits per day/week/month
- **Contributor Activity**: Number of unique contributors over time
- **Issue Resolution Time**: Average time to close issues
- **Pull Request Merge Rate**: Percentage of pull requests that get merged
- **Repository Engagement**: Combined score of stars, forks, and watchers

### Blockchain Events

Blockchain events track on-chain activities, including contract invocations and transactions. The `event_source` is the name of the blockchain, eg, `OPTIMISM`, `BASE`, `ARBITRUM_ONE`, etc.

#### Contract Events

- **CONTRACT_INVOCATION**: Direct invocation of a contract
- **CONTRACT_INTERNAL_INVOCATION**: Internal contract calls

#### Derived Metrics

- **Contract Usage**: Number of contract invocations per day
- **Gas Usage**: Total gas consumed by contract interactions
- **Transaction Volume**: Number of transactions involving a contract
- **User Base**: Number of unique addresses interacting with a contract over a given time period

### ERC-4337 Events (4337)

ERC-4337 events track account abstraction activities on the blockchain.

#### User Operation Events

- **CONTRACT_INVOCATION_VIA_USEROP**: Contract invocation through a user operation
- **CONTRACT_INVOCATION_VIA_PAYMASTER**: Contract invocation through a paymaster
- **CONTRACT_INVOCATION_VIA_BUNDLER**: Contract invocation through a bundler

#### Derived Metrics

- **User Operation Volume**: Number of user operations per day
- **Paymaster Usage**: Percentage of operations using paymasters
- **Bundler Distribution**: Distribution of operations across bundlers

### Funding Events (FUNDING)

Funding events track financial transactions related to open source projects.

#### Financial Events

- **GRANT_RECEIVED_USD**: Receipt of a grant in USD equivalent
- **CREDIT**: Incoming financial transaction (Open Collective)
- **DEBIT**: Outgoing financial transaction (Open Collective)

#### Derived Metrics

- **Funding Volume**: Total funding received over time
- **Funding Sources**: Distribution of funding by source
- **Expense Categories**: Breakdown of expenses by category
- **Funding Sustainability**: Ratio of incoming to outgoing funds

### Dependency Events (DEPS_DEV)

Dependency events track package dependencies and their changes.

#### Dependency Events

- **ADD_DEPENDENCY**: Addition of a new dependency
- **REMOVE_DEPENDENCY**: Removal of an existing dependency
- **DOWNLOADS**: Number of package downloads on a given date

#### Derived Metrics

- **Dependency Growth**: Rate of dependency addition over time
- **Dependency Churn**: Rate of dependency changes
- **Package Popularity**: Download trends over time
- **Dependency Health**: Ratio of active to deprecated dependencies

## Event Schema

---

All events in OSO follow a consistent schema with the following key fields:

| Field                     | Description                                             |
| ------------------------- | ------------------------------------------------------- |
| `time`                    | Timestamp of the event                                  |
| `to_artifact_id`          | ID of the target artifact                               |
| `from_artifact_id`        | ID of the source artifact                               |
| `event_type`              | Type of event (e.g., COMMIT_CODE, CONTRACT_INVOCATION)  |
| `event_source_id`         | Unique identifier for the event source                  |
| `event_source`            | Source of the event (e.g., GITHUB, BLOCKCHAIN)          |
| `to_artifact_name`        | Name of the target artifact                             |
| `to_artifact_namespace`   | Namespace of the target artifact                        |
| `to_artifact_type`        | Type of the target artifact                             |
| `to_artifact_source_id`   | Source ID of the target artifact                        |
| `from_artifact_name`      | Name of the source artifact                             |
| `from_artifact_namespace` | Namespace of the source artifact                        |
| `from_artifact_type`      | Type of the source artifact                             |
| `from_artifact_source_id` | Source ID of the source artifact                        |
| `amount`                  | Numeric value associated with the event (if applicable) |

## Using Events for Analysis

---

Events form the foundation for many OSO metrics and analyses. Raw and processed event data is available to the community via pyoso.

## Examples with pyoso

---

Here are examples of how to use pyoso to access event data:

### GitHub Events Example

```python
import os
import pandas as pd
from pyoso import Client

OSO_API_KEY = os.environ['OSO_API_KEY']
client = Client(api_key=OSO_API_KEY)

# Find the number of unique contributors to a specific repository
query = """
SELECT
  COUNT(DISTINCT from_artifact_name) as unique_contributors
FROM int_events__github
WHERE
  event_source = 'GITHUB'
  AND to_artifact_namespace = 'ethereum'
  AND to_artifact_name = 'go-ethereum'
  AND time >= CURRENT_DATE - INTERVAL '30' DAY
"""
df = client.to_pandas(query)
print(f"Number of unique contributors in the last 30 days: {df['unique_contributors'].iloc[0]}")

# Get daily commit counts
query = """
SELECT
  DATE(time) as day,
  COUNT(*) as commit_count
FROM int_events__github
WHERE
  event_source = 'GITHUB'
  AND event_type = 'COMMIT_CODE'
  AND to_artifact_namespace = 'ethereum'
  AND to_artifact_name = 'go-ethereum'
  AND time >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY DATE(time)
ORDER BY day
"""
df = client.to_pandas(query)
print("\nDaily commit counts:")
print(df)
```

### Blockchain Events Example

```python
import os
import pandas as pd
from pyoso import Client

OSO_API_KEY = os.environ['OSO_API_KEY']
client = Client(api_key=OSO_API_KEY)

# Find the number of transactions for a specific contract on Optimism
query = """
SELECT
  COUNT(*) as transaction_count,
  COUNT(DISTINCT from_artifact_name) as unique_users
FROM int_events__blockchain
WHERE
  event_source = 'OPTIMISM'
  AND event_type = 'CONTRACT_INVOCATION'
  AND to_artifact_name = '0x4200000000000000000000000000000000000006'  -- WETH contract on Optimism
  AND time >= CURRENT_DATE - INTERVAL '7' DAY
"""
df = client.to_pandas(query)
print(f"Number of transactions in the last 7 days: {df['transaction_count'].iloc[0]}")
print(f"Number of unique users: {df['unique_users'].iloc[0]}")

# Get daily transaction counts
query = """
SELECT
  DATE(time) as day,
  COUNT(*) as transaction_count
FROM int_events__blockchain
WHERE
  event_source = 'OPTIMISM'
  AND event_type = 'CONTRACT_INVOCATION'
  AND to_artifact_name = '0x4200000000000000000000000000000000000006'
  AND time >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY DATE(time)
ORDER BY day
"""
df = client.to_pandas(query)
print("\nDaily transaction counts:")
print(df)
```
