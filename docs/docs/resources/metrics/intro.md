---
sidebar_position: 1
---

# Overview

Learn how Open Source Observer creates impact metrics.

Metrics are most commonly queried by project (eg, `uniswap`), although they can also be queried by individual artifact or at the collection level.

## Categories

The following categories of metrics are available:

- [GitHub Activity](./github_activity), including commits, pull requests, issues, and stars for all repositories owned by the project.
- [GitHub Contributors](./github_contributors), including the profile and activity of different types of contributors to the project.
- [Onchain Activity](./onchain_activity), including transaction counts and fees for all smart contracts deployed by the project across supported chains.
- [Onchain Users](./onchain_users), including the number and segmentation of unique addresses that have interacted with the project's smart contracts over different period of time.
- [Node Package Manager (npm) Activity](./npm_activity), including downloads for all packages released by the project.
- [Dependencies](./dependencies), including the number of dependencies and dependents for all packages released by the project.

## Key Terms

The following terms are helpful in understanding how metrics are constructed. In general, a metric is an aggregation of events by artifact, project, or collection. For more details on how these databases are constructed, see here: [Schemas](../../category/schemas).

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

### GitHub

- GIT_REPOSITORY
- GITHUB_ORG
- GITHUB_USER

### Onchain

- EOA_ADDRESS
- DEPLOYER_ADDRESS
- SAFE_ADDRESS
- CONTRACT_ADDRESS
- FACTORY_ADDRESS

### npm

- NPM_PACKAGE

## Event Types

The following event types are currently available:

### Github

- COMMIT_CODE
- ISSUE_CLOSED
- ISSUE_OPENED
- ISSUE_REOPENED
- PULL_REQUEST_CLOSED
- PULL_REQUEST_MERGED
- PULL_REQUEST_OPENED
- PULL_REQUEST_REOPENED

### Onchain

- CONTRACT_INVOCATION_DAILY_COUNT
- CONTRACT_INVOCATION_DAILY_L1_GAS_USED
- CONTRACT_INVOCATION_DAILY_L2_GAS_USED

### npm

- DOWNLOADS

---

To contribute new metrics, please see our guide [here](../../contribute/transform/create-impact-metrics)
