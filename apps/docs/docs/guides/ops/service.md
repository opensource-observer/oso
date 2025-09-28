---
title: OSO Service
sidebar_position: 1
---

The OSO team aims to provide reliable infrastructure as a public good
for the community to build upon.
This document should not be treated as a guarantee of service
or service-level agreement (SLA).
Rather, this document should serve as a reference and shared target
that the community aims to achieve together.

## Service Status

You can find our status page here:

[https://www.opensource.observer/status](https://www.opensource.observer/status)

## Service Definition

OSO is constantly experimenting with new technology and services
to improve our infrastructure.
We only aim to provide service availability for the following mature services:

- [Dagster](https://dagster.opensource.observer)
- [sqlmesh pipeline](https://dagster.opensource.observer/assets/sqlmesh?view=folder)
- [API](https://www.opensource.observer/graphql)
- [Frontend](https://www.opensource.observer)
- [Documentation](https://docs.opensource.observer)

## OSO Data

In addition to services that we maintain, OSO provides data that is not covered
directly by the above services. These data assets are available for querying and
usage within the warehouse and are materialized using dagster or sqlmesh. We
categorize this data into three main types

:::Note
At this time the dagster assets aren't properly grouped. However, once they are
we should use the global asset lineage as the source of truth for asset health.

[See here](https://admin-dagster.opensource.observer/asset-groups)
:::

- [Core Source Data](https://admin-dagster.opensource.observer/locations/default/jobs/materialize_core_assets_job)
  - Project related data (oss-directory, op-atlas)
  - Github data
  - Superchain data
  - Anything labeled `core`
- [Unstable Source Data](https://admin-dagster.opensource.observer/locations/default/jobs/materialize_unstable_source_assets_job)
  - Some external 3rd party data that is not guaranteed to be reliable and may
    change without notice.
  - This is _generally_ experimental data or data that is not necessary to be
    up to date.
- SQLMesh
  - SQLMesh assets are data assets derived from executing sqlmesh models that
    depend on source data.

### A note about data provenance and unstable source data

When querying the OSO data warehouse, it is possible to trace the lineage of
data assets back to their source. This is important for understanding the
context and reliability of the data being used. If the data source being used is
a known "unstable" source, it will be marked as such in the lineage information.

## Service Level Objectives

The following are the internal service level objectives (SLOs) for OSO. These are not guarantees of service, but rather targets for the team to strive towards.

- Core Source Data
  - Description
    - Core data are assets that are necessary for the OSO warehouse to function effectively.
  - Scope
    - All assets labeled `core` and not including sqlmesh assets.
  - Metrics
    - Materialization Reliability:
      - Value
        - 99.0% success rate for 30 days
      - Measurement interval
        - 30 days
      - Description
        - After retries, we should not experience more than 99.0%
          failure rate for processes that materialize data.
    - Data freshness:
      - Value
        - Data should be fresh within some time interval at all times. For
          partitioned data, 99.0% of partitions should be materialized.
      - Measurement interval
        - Point in time
      - Description
        - At any given time, each core data should have a freshness rate within
          some specified time interval. Freshness is determined by the time
          since the last materialization, or by the success data audits for a
          given asset. The time interval should be defined by each asset in the
          asset's configuration. These should be expressed as a time delta.
- Unstable Source Data
  - Description
    - Unstable source data are assets that are not critical to the function of
      the OSO warehouse. They are considered potentially unreliable and have a
      significantly lower service level objective. At this time the only SLOs
      for this data type are related to the infrastructure that supports it. The
      data itself has no guarantees. If any given data asset in this category of
      data falls below the established SLOs, it may be subject to removal from
      the platform.
  - Scope
    - All assets without a `core` label and not including sqlmesh assets
  - Metrics
    - Materialization Reliability:
      - Value
        - 75.0% success rate for 30 days
      - Measurement interval
        - 30 days
      - Description
        - After retries, we should not experience more than 85.0% failure rate
          for processes that materialize data.
- SQLMesh
  - Scope
    - The sqlmesh assets
  - Metrics
    - Materialization Reliability:
      - Value
        - 99.0% success rate
      - Measurement interval
        - 30 days
      - Description
        - Regardless of retries, we should not experience more than 99.0% failure rate for sqlmesh.
  - Other notes
    - SQLMesh data audits are all-or-nothing, so they must pass or a sqlmesh materialization will fail.
- Public Applications
  - Scope
    - [Dagster](https://dagster.opensource.observer)
    - [sqlmesh pipeline](https://dagster.opensource.observer/assets/sqlmesh?view=folder)
    - [API](https://www.opensource.observer/graphql)
    - [Frontend](https://www.opensource.observer)
    - [Documentation](https://docs.opensource.observer)
  - Metrics
    - Availability
      - Value
        - 99.0% availability
      - Measurement interval
        - 30 days
      - Description
        - Services should be available 99.0% of the time.
    - Requests
      - Value
        - 99.0% request success rate
      - Measurement interval
        - 30 days
      - Description
        - 99.0% of all requests should not result in an error.
- Consumer Trino
  - Scope
    - Public facing trino (`opensource.observer/api/v1/sql`)
  - Metrics
    - Availability
      - Value
        - 99.0% availability
      - Measurement interval
        - 30 days
      - Description
        - Services should be available 99.0% of the time.
    - Queries
      - Value
        - 90.0% query success rate
      - Measurement interval
        - 30 days
      - Description
        - 90.0% of all queries should not result in an unexpected error. User errors are ignored in this measurement.
- Kubernetes Infrastructure
  - Scope
    - Kubernetes clusters and resources. This is an internal only resource,
      but it is critical for the operation of our services. The availability
      of this infrastructure directly impacts the reliability of our
      services.
  - Metrics
    - Availability
      - Value
        - 99.0% availability
      - Measurement interval
        - 30 days
      - Description
        - Kubernetes infrastructure should be available 99.0% of the time.
    - Flux
      - Value
        - 99.0% availability
      - Measurement interval
        - 30 days
      - Description
        - Flux should be available 99.0% of the time.

### SLO Policy

Any service that does not meet its SLOs will trigger a remedial sprint to address the issues and bring the service back into compliance with the SLOs. Remedial sprints will continue until the service or data is back in compliance with the SLO.

## Outage Escalation

The best way to get in touch with the team is via
[Discord](https://www.opensource.observer/discord).
