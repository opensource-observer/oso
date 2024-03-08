---
title: Impact Vector Specification
sidebar_position: 3
---

An impact vector is a direction of positive impact that a collection of similar projects in an open source ecosystem should work towards. Each vector represents:

- a quantitative impact metric (eg, a project’s contribution to sequencer fees)

- measured over a discrete period of time (eg, the last 6 months)

- normalized across a distribution of projects in the ecosystem (eg, all projects with onchain deployments)

:::warning
This page is a work in progress.
:::

## Creating Impact Vectors

### Name the vector

Choose a name that is descriptive and easy to remember.

### Define the metric and time period

Choose a metric that is relevant to the vector and can be calculated via a [dbt transform](./metrics).

Choose a period of time that is long enough to be meaningful and relevant to the analysis.

Apply these filters to arrive at a selection of projects that are relevant to the impact vector.

### Normalize the data and set performance levels

Choose a normalization method that is easy to calculate and appropriate for the metrics. Typically this is a Gaussian distribution or a log scale.

Choose performance targets based on the normalized distribution. For example, an "exceptional" project might be in the top 5% of the distribution.

### Submit Your Impact Vector

Submit your impact vector to the [OSO Data Collective](https://www.opensource.observer/data-collective) for review and inclusion in the OSO data warehouse.

## Examples of Impact Vectors

The following are examples of impact vectors that could be used to measure the impact of a collection of OSS projects in an open source crypto ecosystem.

- Grow full-time developers. Measured by full-time developer months since the project's first commit.

- Expand the open source community. Measured by GitHub users who made their contribution to a project in the last 6 months.

- Support modular, permissionless contributions. Measured by highest fork count among repos owned by the project.

- Be beloved in the community. Measured by stars received from other developers in a given collection of projects.

- Make it easier to build awesome apps. Measured by NPM downloads over last 6 months.

- Grow sequencer fees. Measured by all-time Layer 2 gas fees.

- Increase onchain activity. Measured by all-time transactions on the network.

- Grow ‘active users. Measured by multi-app users on the network with more than 30 total transactions and some activity in the last 90 days.
