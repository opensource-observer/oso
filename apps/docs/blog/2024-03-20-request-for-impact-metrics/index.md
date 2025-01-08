---
slug: request-for-impact-metrics
title: "Request for Impact Metrics"
authors: [ccerv1]
tags: [community, kariba]
image: ./cycle.jpeg
---

Over the past few months, we've been hard at work creating the infrastructure to collect and analyze impact metrics for open source projects. We're excited to announce that we're ready to start doing some new analysis on data from open source projects ... and we need your help!

This post includes some of the domains we're interested in exploring as well as an initial list of impact metrics we'd like to collect. We're looking for feedback on these metrics and suggestions for additional metrics we should consider. We're also looking for contributors to help us apply these impact metrics.

## Get Involved

If you'd like to get involved, here's what to do:

1. Apply to [join the Data Collective](https://www.kariba.network/). It only takes a few minutes. We'll review, and reach out to schedule an onboarding call.
2. Join our [Discord server](https://www.opensource.observer/discord) and say hello.
3. Get inspiration from our Colab directory of [starter notebooks for impact metrics](https://drive.google.com/drive/folders/1I4exiLfZYgPwIGBEzuAMeGtJUhtS_DE7?usp=drive_link). We also have of them in our [Insights repo](https://github.com/opensource-observer/insights/tree/main/community/notebooks) if you prefer to run them locally.
4. Consult [our docs](../../docs/) and especially our [impact metric spec](../../docs/references/impact-metrics/) as you prepare your analysis.

The rest of this post includes more details on the types of impact metrics we're interested in.

<!-- truncate -->

## Areas of Interest

At a high level, we're interested in the following types of impact metrics being applied to the OSO dataset:

- **Project Health**: Metrics that capture the momentum and activity of a project's contributor community and codebase.
- **Onchain Reputation**: Metrics that attempt to differentiate onchain users based on behavior and trust scores.
- **Contributor Reputation**: Metrics that attempt to differentiate code contributors based on behavior and PageRank-style scoring.
- **Ecosystem Impact**: Metrics that capture the impact of a project on the broader health of an open source ecosystem, ie, as a "talent feeder" or "dependency" for other projects.
- **Project Metadata**: Metrics that capture the licensing and open sourciness of a project.
- **Domain-specific Impact**: Metrics that are relevant only to a specific domain, such as "defi" or "consumer", for onchain projects.

## Metrics by Category

Here's a working list of impact metrics we're interested in collecting, including links or ideas for how to calculate them. We've flagged a few that are good first issues for contributors to work on.

### Project Health

Metrics that capture the momentum and activity of a project's contributor community.

The inspiration for these metrics comes from the [CHAOSS Community](https://chaoss.community), which has cataloged a large suite of metrics for open source projects but is not prescriptive in how they should be calculated. We're interested in applying these same metrics to the OSO dataset and experimenting with different calculation and filtering approaches. A number of these are "good first issues" for contributors to work on because the data is ready to go and they are well-documented on the CHAOSS website. Have a look at [Bus Factor](https://chaoss.community/kb/metric-bus-factor/) and [Burstiness](https://chaoss.community/kb/metric-burstiness/) for inspiration.

| Impact Metric       | Description                                                                                                                               | Comments                                |
| :------------------ | :---------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------- |
| Bus Factor          | How high is the risk to a project should the most active people leave?                                                                    | Good first issue                        |
| Burstiness          | How are short timeframes of intense activity, followed by a corresponding return to a typical pattern of activity, observed in a project? | Good first issue                        |
| Velocity            | What is the development speed for an organization?                                                                                        | Good first issue                        |
| Self-merge rates    | What is the rate of self-merges in a project?                                                                                             | Requires more indexing of PR threads    |
| Issue Response Time | How much time passes between the opening of an issue and a response in the issue thread from another contributor?                         | Requires more indexing of issue threads |

:::tip
Check out our [starter notebooks](https://drive.google.com/drive/folders/1I4exiLfZYgPwIGBEzuAMeGtJUhtS_DE7?usp=drive_link) for impact metrics including Bus Factor and Velocity. The current Bus Factor for Open Source Observer is 0.36 - a good deal lower than the average in our dataset (0.60), but not as low as Ethereum / Protocol Guild (0.05).
:::

### Onchain Reputation

_Metrics that attempt to differentiate onchain users based on behavior and trust scores._

This is a hot topic right now, with a number of projects attempting to create reputation systems for onchain users. We're integrating with many of the leading projects and bringing the data they generate into the OSO data warehouse. From there, there are all sorts of directions you can take the analysis!

The **Onchain Activity** metric is a good starting point for new analysts. Have a look at our working definitions for [onchain users](../../docs/references/impact-metrics/onchain) and help us create some better ones. The **Network Loyalty** is a spicy metric that will get even spicier as we add more networks to the OSO dataset!

| Impact Metric    | Description                                           | Comments                                   |
| :--------------- | :---------------------------------------------------- | :----------------------------------------- |
| Onchain Activity | How active is the user onchain?                       | Good first issue                           |
| Network Loyalty  | How much of a user's activity is on a single network? | Good first issue                           |
| User Segment     | What kind of dapps is the user most interested in?    | Good first issue                           |
| ENS History      | Does the user have a rich profile on ENS?             | Requires indexing of ENS data              |
| Gitcoin Passport | Does the user have a high Gitcoin passport score?     | Requires indexing of Gitcoin Passport data |

When working with these metrics, because they deal with LOTS of transactions, it may be helpful to grab a bunch of data in a single query request and then do further analysis in a notebook. For example, this query will grab each user's transactions with each project on each network in the last 90 days:

```sql
-- Get the number of txns by user / project / network / day
SELECT
  project_id,
  from_name AS user_address,
  to_namespace AS network,
  time,
  SUM(amount) AS txns
FROM `oso.int_events_to_project`
WHERE time >= DATE_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
AND event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
GROUP BY 1,2,3,4
```

:::tip
Check out our [starter notebooks](https://drive.google.com/drive/folders/1I4exiLfZYgPwIGBEzuAMeGtJUhtS_DE7?usp=drive_link) for impact metrics including onchain activity and network loyalty.
:::

### Contributor Reputation

_Metrics that attempt to differentiate code contributors based on behavior and PageRank-style scoring._

These metrics are useful for measuring impact _within_ a project and for measuring the influence of a contributor _across_ projects. For inspiration, check out the [CHAOSS Community](https://chaoss.community) and [SourceCred](https://sourcecred.io/docs).

| Impact Metric             | Description                                                                       | Comments                                            |
| :------------------------ | :-------------------------------------------------------------------------------- | :-------------------------------------------------- |
| Contributor Concentration | How much of a contributor's activity is on a single project?                      | Good first issue                                    |
| Conversion Rate           | What are the rates at which new contributors become more sustained contributors?  | Good first issue                                    |
| Maintainer Score          | What characteristics of a contributor's activity make them a reliable maintainer? | Good first issue                                    |
| PageRank                  | What is the PageRank of a contributor? Choose your own implementation!            | Good first issue                                    |
| MVPR                      | What is the most valuable pull request?                                           | Requires more indexing of related GitHub event data |

The **Contributor Concentration** is a good first issue for new analysts, as it's less open-ended and can take advantage of the built-in developer categories included in the `int_devs` table:

```sql
-- Get the number of months each developer has been active on each project
SELECT
  project_id,
  from_id AS user_id,
  SUM(CASE WHEN user_segment_type = 'FULL_TIME_DEV' THEN amount END) AS full_time_dev_months,
  SUM(CASE WHEN user_segment_type = 'PART_TIME_DEV' THEN amount END) AS part_time_dev_months,
  SUM(CASE WHEN user_segment_type = 'OTHER_CONTRIBUTOR' THEN amount END) AS other_contributor_months
FROM `oso.int_devs`
GROUP BY 1,2
```

The **PageRank** metric is another fun rabbithole to go down. For inspiration, check out some of the work we've done previously in our [Insights repo](https://github.com/opensource-observer/insights/tree/main/community/bounties/page_rank_rpgf3) and the pioneering work of [SourceCred](https://sourcecred.io/docs).

:::tip
Check out our [starter notebooks](https://drive.google.com/drive/folders/1I4exiLfZYgPwIGBEzuAMeGtJUhtS_DE7?usp=drive_link) for impact metrics including contributor concentration and page rank.
:::

### Ecosystem Impact

_Metrics that capture the impact of a project on the broader health of an open source ecosystem, ie, as a "talent feeder" or "dependency" for other projects._

These metrics zoom out and seek to understand a project's influence within a broader open source ecosystem. One angle to consider is the role of "feeder" projects, ie, projects where users and/or contributors first enter the ecosystem and then go on to contribute to or use other projects. Another angle is the role of "dependency" projects, ie, projects that are imported by other projects in their dependency tree. As of now, we don't have our dependency data indexed, but we're working on it!

| Impact Metric         | Description                                                                                 | Comments                          |
| :-------------------- | :------------------------------------------------------------------------------------------ | :-------------------------------- |
| Contributor Feeder    | How many contributors has the project onboarded that go on to contribute to other projects? | Good first issue                  |
| User Feeder           | How many onchain users has the project onboarded that go on to use other projects?          | Good first issue                  |
| Elephant Factor       | How many projects depend on this project?                                                   | Requires indexing dependency data |
| Downstream Fees       | How much in sequencer fees are contributed by projects that are dependents of this project? | Requires indexing dependency data |
| Downstream Users      | How many onchain users are using this project as a dependency?                              | Requires indexing dependency data |
| Downstream Developers | How many developers are using this project as a dependency?                                 | Requires indexing dependency data |
| Network Centrality    | How central is this project to the network?                                                 | Requires indexing dependency data |

The contributor and user "feeder" metrics are good first issues for new analysts.

:::tip
Check out our [starter notebooks](https://drive.google.com/drive/folders/1I4exiLfZYgPwIGBEzuAMeGtJUhtS_DE7?usp=drive_link) for contributor and user "feeders".
:::

### Project Metadata

_Metrics that capture relevant metadata about the licensing and open sourciness of a project._

Project metadata metrics consider the [licensing practices](https://opensource.org/licenses) and the open source nature of projects. By examining **License Coverage**, **OSI Approved Licenses**, and **Drips Access**, we gain insights into a project's commitment to open source principles and its accessibility to the community. [Drips](https://docs.drips.network/) is an amazing new way of easily streaming money to any open source project if they have a `funding.json` file in their repo.

| Impact Metric         | Description                                                                    | Comments                                |
| :-------------------- | :----------------------------------------------------------------------------- | :-------------------------------------- |
| License Coverage      | How much of the code base has declared licenses?                               | Requires more indexing of repo metadata |
| OSI Approved Licenses | What percentage of a project’s licenses are OSI approved open source licenses? | Requires more indexing of repo metadata |
| Drips Access          | Does the project have a `funding.json` file?                                   | Requires more indexing of repo metadata |

### Domain-specific Impact

_Metrics that are relevant only to a specific domain, such as "DeFi" or "consumer", for onchain projects._

The first step in this process is to define a domain and create a list of projects that are relevant to that domain. For example:

```sql
-- Sample of DeFi projects
SELECT *
FROM `oso.onchain_metrics_by_project_v1`
WHERE project_name IN ('Uniswap', '1inch', 'Sushi')
```

From there, any of the above metrics (as well as our existing onchain impact metrics) can be applied to the projects in that domain.

This is a good first issue for people with domain expertise who are able to curate a list of projects relevant to a specific domain.

## Submitting Your Impact Metrics

If you've created a new impact metric, we'd love to see it! We'll implement the best ones as new data models and make them available to everyone in the community.

You can submit your impact metric to the OSO core team by posting it in our [Discussions forum](https://github.com/opensource-observer/oso/discussions/1090). Contributions should include the following:

- Name of impact metric
- Brief description of your calculation steps
- Link to your code (eg, Colab or Jupyter notebook)
- Chart or table showing the metric applied to a set of projects

If you run into issues or have questions, let us know on [Discord](https://www.opensource.observer/discord).

We're excited to see what you come up with!
