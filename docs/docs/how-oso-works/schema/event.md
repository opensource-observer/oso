---
title: Event
sidebar_position: 5
---

:::info
An **event** is a record of a transaction or other activity involving an artifact, or a snapshot of cumulative events at a given point in time. Events are used to track the history of an artifact.
:::

## Event Types

---

Event types are used to classify activities that related in a given artifact namespace. The following event types are currently supported:

### GitHub Events

All GitHub events are associated with a unique GitHub repository and GitHub user. The following GitHub events are currently supported:

- Commit Code: An event that records a commit to a GitHub repository on the main branch, including the author, timestamp, and commit url.
- Pull Request Opened: An event that records the creation of a pull request, including the author of the pull request, timestamp, and pull request url.
- Pull Request Approved: An event that records the approval of a pull request, including the user approving the pull request, timestamp, and pull request url.
- Pull Request Merged: An event that records the merging of a pull request, including the user performing the merge, timestamp, and pull request url.
- Issue Opened: An event that records the creation of an issue, including the author of the issue, timestamp, and issue url.
- Issue Closed: An event that records the closing of an issue, including the user closing the issue, timestamp, and issue url.
- Starred: An event that records the starring of a GitHub repository, including the user starring the repository, timestamp, and repository url.
- Star Aggregate Stats: A snapshot of the number of stars for a GitHub repository on a given date.
- Forked: An event that records the forking of a GitHub repository, including the user forking the repository, timestamp, and repository url.
- Fork Aggregate Stats: A snapshot of the number of forks for a GitHub repository on a given date.
- Watcher Aggregate Stats: A snapshot of the number of watchers for a GitHub repository on a given date.

### NPM Events

All NPM events are associated with a unique NPM package. The following NPM events are currently supported:

- Downloads: A snapshot of the number of downloads for an NPM package on a given date.

### Blockchain Events

All blockchain events are associated with a unique blockchain address-network pair. The following blockchain events are currently supported:

- Funding: An event that records the transfer of grant funds to a blockchain `wallet` address, including the amount, sender address, timestamp, and other details.
- Contract Invoked: An event that records a user transacting with a smart contract, including the number of transactions, user address, timestamp, and other details.
- Contract Invocation Daily Count: A snapshot of the number of transactions made with a contract address on a given date.
- Contract Invocation Daily Fees: A snapshot of the fees paid for transactions made with a contract address on a given date.
- Users Interacted: A snapshot of the number of unique users (addresses) transacting with a contract address on a given date.

## Querying Event Data

---

The event table is the largest table in the OSO Data Warehouse. As such, we have created data marts that aggregate event data at daily, weekly, and monthly intervals for artifacts, projects, and collections.

As event queries may be slow, we recommend using these aggregate tables whenever possible. See the [API documentation](../../integrate) for more information about querying event data.
