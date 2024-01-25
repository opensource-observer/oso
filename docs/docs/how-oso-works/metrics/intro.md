---
sidebar_position: 1
---

# Impact Metrics

> This document provides details on Open Source Observer's impact metrics. Metrics are typically queried by project (eg, `uniswap`), although they can also be queried by individual artifact.

## Categories

The following categories of metrics are available:

- [GitHub Code Contribution Metrics](./github_contributions.md), including commits, pull requests, issues, and stars for all repositories owned by the project.
- [Developer Metrics](./developers.md), including the profile and activity of different types of contributors to the project.
- [Onchain Metrics](./onchain.md), including transaction counts, fees, and users for all smart contracts deployed by the project across supported chains.
- [Node Package Manager (npm) Metrics](./npm.md), including downloads for all packages released by the project.
- [Dependency and Dependent Metrics](./dependents.md), including the number of dependencies and dependents for all packages released by the project.

## Key Terms

### Artifact

An artifact is a single entity that can be tracked by Open Source Observer. For example, a GitHub repo, a smart contract, or an npm package. An artifact can only belong to one project. However, not all artifacts must belong to a project. Information about artifacts is contained in their `name`, `namespace`, and `type`.

### Project

A project is a collection of related artifacts. For example, the Uniswap project includes the Uniswap v2 and Uniswap v3 artifacts. A project must contain at least one GitHub repo in order to be instantiated. A project is referred to by its slug, which is usually the name of the project in lowercase and without spaces.

### Collection

A collection is a group of related projects. For example, a DeFi collection might include the Uniswap, Compound, and Aave projects. A collection must contain at least one project in order to be instantiated.

### Event

An event is a single action between artifiacts that is tracked by Open Source Observer. For example, a commit, a pull request, or a transaction. Every event must have a `typeId` (see definations below), a `time`, a `fromId` (pointing to an artifact), and a `toId` (pointing to another artifact)

## Artifact Types

The following are some of the artifact types tracked by Open Source Observer:

- Onchain: 'EOA_ADDRESS', 'SAFE_ADDRESS', 'CONTRACT_ADDRESS', 'FACTORY_ADDRESS'
- GitHub: 'GIT_REPOSITORY', 'GITHUB_ORG', 'GITHUB_USER'
- npm: 'NPM_PACKAGE'

## Event Types

The following event `typeId`s are most commonly used:

```
'FUNDING': 1,
'PULL_REQUEST_CREATED': 2,
'PULL_REQUEST_MERGED': 3,
'COMMIT_CODE': 4,
'ISSUE_CLOSED': 6,
'DOWNSTREAM_DEPENDENCY_COUNT': 7,
'UPSTREAM_DEPENDENCY_COUNT': 8,
'DOWNLOADS': 9,
'CONTRACT_INVOKED': 10,
'USERS_INTERACTED': 11,
'CONTRACT_INVOKED_AGGREGATE_STATS': 12,
'PULL_REQUEST_CLOSED': 13,
'STAR_AGGREGATE_STATS': 14,
'PULL_REQUEST_APPROVED': 17,
'ISSUE_CREATED': 18,
'STARRED': 21,
'FORK_AGGREGATE_STATS': 22,
'FORKED': 23,
'CONTRACT_INVOCATION_DAILY_COUNT': 25,
'CONTRACT_INVOCATION_DAILY_FEES': 26
```
