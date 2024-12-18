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

All sources of event data are associated with a unique `event_source`. We are adding new event sources all the time. The current event sources can be viewed [here](https://models.opensource.observer/#!/model/model.opensource_observer.int_events#depends_on). The full events DAG can be viewed [here](https://models.opensource.observer/#!/model/model.opensource_observer.int_events?g_v=1&g_i=%2Bint_events%2B).

## Currently Supported Event Types

---

Event types are used to classify activities that relate to a given artifact namespace. The following event types are currently supported:

### COMMIT_CODE

Represents a commit made to a code repository. This event is used to track changes in the source code over time.

### CONTRACT_INVOCATION_DAILY_COUNT

Represents the daily count of contract invocations. This event is used to track the frequency of contract interactions on the blockchain.

### CONTRACT_INVOCATION_DAILY_L2_GAS_USED

Represents the total gas used in contract invocations on Layer 2 networks on a daily basis. This event helps track the resource consumption of contract executions.

### CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT

Represents the daily count of successful contract invocations. This event is used to measure the success rate of contract executions on the blockchain.

### FORKED

Represents the event when a repository is forked. This event is used to track the distribution and branching of the source code.

### ISSUE_CLOSED

Represents the closing of an issue in a repository. This event is used to track the resolution and management of reported issues.

### ISSUE_OPENED

Represents the opening of a new issue in a repository. This event is used to track new problems or feature requests reported by users.

### ISSUE_REOPENED

Represents the reopening of a previously closed issue in a repository. This event is used to track the reoccurrence or unresolved status of issues.

### PULL_REQUEST_CLOSED

Represents the closing of a pull request in a repository. This event is used to track the finalization and rejection of proposed code changes.

### PULL_REQUEST_MERGED

Represents the merging of a pull request into the main branch of a repository. This event is used to track the integration of code changes.

### PULL_REQUEST_OPENED

Represents the opening of a new pull request in a repository. This event is used to track proposed changes to the codebase.

### PULL_REQUEST_REOPENED

Represents the reopening of a previously closed pull request in a repository. This event is used to track the reconsideration of proposed code changes.

### STARRED

Represents the starring of a repository by a user. This event is used to track the popularity and user interest in the repository.

## NPM Events

:::warning
This section is currently in development.
:::

All NPM events are associated with a unique NPM package. The following NPM events are currently supported:

- Downloads: A snapshot of the number of downloads for an NPM package on a given date.
