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

### Code Events

These events track activities related to source code management and collaboration:

#### COMMIT_CODE

Represents a commit made to a code repository. This event is used to track changes in the source code over time.

#### FORKED

Represents the event when a repository is forked. This event is used to track the distribution and branching of the source code.

#### RELEASE_PUBLISHED

Represents the publication of a new release version of the software.

#### STARRED

Represents the starring of a repository by a user. This event is used to track the popularity and user interest in the repository.

### Issue Events

These events track the lifecycle of issues in a repository:

#### ISSUE_OPENED

Represents the opening of a new issue in a repository. This event is used to track new problems or feature requests reported by users.

#### ISSUE_CLOSED

Represents the closing of an issue in a repository. This event is used to track the resolution and management of reported issues.

#### ISSUE_REOPENED

Represents the reopening of a previously closed issue in a repository. This event is used to track the reoccurrence or unresolved status of issues.

#### ISSUE_COMMENT

Represents a comment made on an issue in a repository.

### Pull Request Events

These events track the lifecycle of pull requests:

#### PULL_REQUEST_OPENED

Represents the opening of a new pull request in a repository. This event is used to track proposed changes to the codebase.

#### PULL_REQUEST_CLOSED

Represents the closing of a pull request in a repository. This event is used to track the finalization and rejection of proposed code changes.

#### PULL_REQUEST_MERGED

Represents the merging of a pull request into the main branch of a repository. This event is used to track the integration of code changes.

#### PULL_REQUEST_REOPENED

Represents the reopening of a previously closed pull request in a repository. This event is used to track the reconsideration of proposed code changes.

#### PULL_REQUEST_REVIEW_COMMENT

Represents a comment made during the review of a pull request.

### Onchain Events

These events track blockchain-related activities:

#### CONTRACT_INVOCATION_DAILY_COUNT

Represents the daily count of contract invocations. This event is used to track the frequency of contract interactions on the blockchain.

#### CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT

Represents the daily count of successful contract invocations. This event is used to measure the success rate of contract executions on the blockchain.

#### CONTRACT_INVOCATION_DAILY_L2_GAS_USED

Represents the total gas used in contract invocations on Layer 2 networks on a daily basis. This event helps track the resource consumption of contract executions.

### Financial Events

These events track financial transactions:

#### GRANT_RECEIVED_USD

Represents the receipt of a grant in USD equilvalent; currently only available for sources listed in [oss-funding](https://github.com/opensource-observer/oss-funding).

#### CREDIT

Represents an incoming financial transaction or credit to an account; currently only available for Open Collective.

#### DEBIT

Represents an outgoing financial transaction or debit from an account; currently only available for Open Collective.

### Dependency Events

These events track package dependencies:

#### ADD_DEPENDENCY

Represents the addition of a new dependency to a project.

#### DOWNLOADS

Represents the number of downloads for a package on a given date according to the package manager's public data.
