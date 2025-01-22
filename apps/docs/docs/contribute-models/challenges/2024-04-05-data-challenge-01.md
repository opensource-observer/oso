---
title: OSO Data Challenge 01
sidebar_position: 8
---

# Earn OP rewards for proposing onchain impact metrics

## Objective

The objective of this challenge is to identify 15-20 metrics that quantify onchain impact effectively. The most useful metrics are intended to be accessible to Optimism badgeholders through [impact calculator apps](https://github.com/orgs/ethereum-optimism/projects/31/views/3?pane=issue&itemId=50124302) during [Retro Funding Round 4](https://optimism.mirror.xyz/nz5II2tucf3k8tJ76O6HWwvidLB6TLQXszmMnlnhxWU).

## Context

To date, most of OSO’s work has been focused on measuring off-chain impact (eg, via GitHub data). The onchain data we’ve aggregated has been pretty surface-level - transaction counts, user numbers, L2 gas fees, etc. Now, we are transitioning to focus more on onchain impact. We are in the process of onboarding new OP chains, integrating with top sources of onchain reputation data, and expanding our project registries. We are also creating documentation, tutorials, and playground datasets to help new analysts get going as quickly as possible.

The goal: get better metrics for tracking onchain impact.

This is the first of hopefully several data challenges focused on onchain impact we’ll be running in the first half of 2024.

## Definitions

An “impact metric” is essentially a SQL query made against the OSO dataset that enables a user to make objective comparisons of impact among projects.

As an example, here’s a very simple onchain impact metric that sums all of a project’s transactions on OP Mainnet over the last 6 months.

```sql
SELECT
  project_id,
  SUM(amount) AS txns_6_months
FROM `opensource-observer.oso.rf4_events_daily_to_project`
WHERE
  event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
  AND DATE(bucket_day) >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH)
GROUP BY project_id
```

A valid impact metric response should contain a `project_id` and `impact_metric` value for each project (with a null value for non-evaluable projects). In the example above, the result would be a set of records containing `project_id` and `txns_6_months` values.

## Challenge Description

This challenge is focused on creating impact metrics for projects that have contracts deployed across the Optimism Superchain.

### Focus Areas

Specifically, we care about impact metrics in the following focus areas:

- **User quality**. Metrics that help measure the quality of a project’s user base, potentially derived from identity primitives (eg, [ENS](https://docs.ens.domains/registry/eth)), trust scores (eg, [Gitcoin Passport](https://docs.passport.gitcoin.co/building-with-passport/passport-api/overview), [EigenTrust](https://docs.karma3labs.com/eigentrust)), social graphs (eg, [Farcaster](https://docs.farcaster.xyz/), [Lens](https://docs.lens.xyz/docs/public-big-query), NFT communities), onchain transaction patterns (eg, frequency, volume of transactions), etc.
- **User growth**. Metrics that evaluate a project's effectiveness in onboarding new users, retaining users, enhancing daily / monthly active users, diversifying onchain activities, etc.
- **Network growth**. Metrics that consider a project’s contributions to sequencer fees, blockspace demand, assets remaining on L2s, etc.
- **Domain-specific performance**: Metrics that are only applicable to a subset of onchain projects in a related domain, such as defi, consumer, NFTs, gaming, etc.

### Requirements

To be considered eligible for the challenge, an impact metric must fulfill the following requirements:

- Be expressed **in SQL** using OSO datasets on BigQuery.
- Quantitatively measure impact on a **continuous scale** by utilizing counts, sums, averages, maxes, or other array functions.
- Aggregate performance over **specific time intervals**, such as the last 90 days, last 180 days, or since project inception.
- Clearly document the **business logic** via code comments, so metrics are easy to read and potentially fork.
- Be composable **across the Superchain**, covering mainnets such as Optimism, Base, Zora, Mode, etc. as we add them to OSO.

### Limitations

There are several limitations in our data model that we don’t expect contributors to solve for:

- An onchain event may only belong to one project. For now, we attribute the impact of any onchain event to the project that deployed the contract. In the future, we may consider other methods of attribution, e.g., attributing which frontend the user interacted with, which dependencies are upstream of the dapp the user interacted with, which project deployed the token that a user is interacting with through a contract, etc.
- Every Ethereum `from` address counts as a user. Of course, many people control more than one Ethereum address. And some `from` addresses are contracts. Until we have indexed data on address characteristics, it is OK for contributors to assume every unique address is a distinct user.

## How to Participate

Here’s what you need to do to participate in this (and future) data challenges.

1. Join the [Kariba Data Collective](https://www.kariba.network/). Participation is open to anyone in the data collective (free to join, but we review applications).
2. Join our Discord and receive a **_data-collective_** role; ask questions and share code snippets in the **_#data-challenges_** channel.
3. Bookmark [our docs and tutorials](../../references/impact-metrics/) for creating impact metrics. Also make sure to browse our [Colab Notebooks](https://drive.google.com/drive/folders/1mzqrSToxPaWhsoGOR-UVldIsaX1gqP0F) for examples and inspiration.
4. Submit your impact metric(s) by opening an issue on our Insight repo [here](https://github.com/opensource-observer/insights/issues/new/choose).

Every impact metric submission should include:

- Metric name
- Keyword tags
- A brief metric description (2-3 sentences)
- SQL code block
- Optional: link to script/notebook or longer form write-up about the metric

As a participant, you may submit up to 10 impact metrics for review. If you have more than 10 ideas, pick your best 10.

## Retroactive Rewards

A total of **3000 OP** is available as retroactive rewards in the form of L2 tokens (OP or USDC) for work on this data challenge.

The primary way to receive rewards is to submit an impact metric in the form described above. We will reward the contributors who come up with the best metrics with 20-50 OP tokens per metric (capped at 10 metrics per contributor). The actual amount of the reward will be a function of the complexity and utility of the metric. As a guiding principle, we want to incentivize contributors to work on hard but widely applicable metrics. (Basically, we don’t want to see 10 variants of daily active users.)

In addition to direct work on impact metrics, we also have reward budgets for work on collections (defining a group of related projects) and adding/updating project data. We will reward collection creators 10-20 OP per new collection that gets added to oss-directory. We will reward contributors of project data at the rates described in our [bounty program](https://docs.opensource.observer/docs/contribute/challenges/bounties#ongoing-bounties) at the prevailing OP-USDC dex rate on May 31. These are capped at 250 OP per contributor.

Finally, we have a reward pool for other forms of contribution during the life of the challenge. This could include efforts to onboard or process new datasets, community activation, and improvements to OSO’s underlying infrastructure.

## Timing

The window for participating in this challenge is open until May 31, 2024 11:59PM UTC. Work submitted after the deadline will NOT be reviewed. Feedback may be provided to work submitted before the deadline. Final reward amounts will be determined on June 7.
