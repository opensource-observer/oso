---
title: Indexers
sidebar_position: 3
---

OSO maintains a suite of indexers that extract and transform data from various sources.

There are three main types indexers that OSO maintains:

1. Import OSS Directory
2. Data Oracles
3. Backfills

## Import OSS Directory

Whenever a project is added or updated in the OSS Directory, its artifacts are indexed and stored in the data warehouse. This includes traversing the project's GitHub repos and dependencies, and tracing all contracts downstream of its deployer addresses.

Once the artifacts have been imported to OSO, their event data will be included in all subsequent data indexing jobs.

## Data Oracles

Data Oracles capture real-time event data from sources like GitHub, NPM, and blockchain networks. These indexers run continuously to capture new events as they occur and add them to the data warehouse.

## Backfills

Backfills are used to fill in historical data that was missed by the Data Oracles. They are run periodically to ensure that the data warehouse is up-to-date and complete.

They are updated and added to OSO by members of the Data Collective.

## WIP

- How to obtain coverage and completeness stats
- Other SLAs
