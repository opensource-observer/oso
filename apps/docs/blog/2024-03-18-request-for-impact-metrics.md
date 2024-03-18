---
slug: request-for-impact-metrics
title: "Request for Impact Metrics"
authors: [ccerv1]
tags: [data collective, impact data science, kariba]
---

Over the past few months, we've been hard at work creating the infrastructure to collect and analyze impact metrics for open source projects. We're excited to announce that we're ready to start doing some new analysis on data from open source projects ... and we need your help!

This post includes some of the domains we're interested in exploring as well as an initial list of impact metrics we'd like to collect. We're looking for feedback on these metrics and suggestions for additional metrics we should consider. We're also looking for contributors to help us apply these impact metrics.

## Get Involved

If you'd like to get involved, here's what to do:

1. Apply to [join the Data Collective](https://www.kariba.network/). It only takes a few minutes. We'll review, and reach out to schedule an onboarding call.
2. Join our [Discord server](https://www.opensource.observer/discord) and say hello.
3. Get inspiration from our Colab directory of [starter notebooks for impact metrics](https://drive.google.com/drive/folders/1I4exiLfZYgPwIGBEzuAMeGtJUhtS_DE7?usp=drive_link).
4. Consult [our docs](https://docs.opensource.observer/docs/) and especially our [impact metric spec](https://docs.opensource.observer/docs/how-oso-works/impact-metrics/) as you prepare your analysis.

The rest of this post includes more details on the types of impact metrics we're interested in.

<!-- truncate -->

## Areas of Interest

At a high level, we're interested in the following types of impact metrics being applied to the OSO dataset:

- **Project Health**: Metrics that capture the momentum and activity of a project's contributor community and codebase.
- **Project Licensing**: Metrics that capture the licensing and open sourciness of a project.
- **Onchain Reputation**: Metrics that attempt to differentiate onchain users based on behavior and trust scores.
- **Contributor Reputation**: Metrics that attempt to differentiate code contributors based on behavior and PageRank-style scoring.
- **Ecosystem Impact**: Metrics that capture the impact of a project on the broader health of an open source ecosystem, ie, as a "talent feeder" or "dependency" for other projects.
- **Domain-specific Onchain Impact**: Metrics that are relevant only to a specific domain, such as "defi" or "consumer", for onchain projects.

## Working List of Impact Metrics

Here's a working list of impact metrics we're interested in collecting, including links or ideas for how to calculate them. We've flagged a few that are good first issues for contributors to work on.

### Project Health

Metrics that capture the momentum and activity of a project's contributor community.

| Impact Metric      | Description                                                                                                                               | Inspiration                                             | Comments                                |
| :----------------- | :---------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------ | :-------------------------------------- |
| Bus Factor         | How high is the risk to a project should the most active people leave?                                                                    | https://chaoss.community/kb/metric-bus-factor/          | Good first issue                        |
| Burstiness         | How are short timeframes of intense activity, followed by a corresponding return to a typical pattern of activity, observed in a project? | https://chaoss.community/kb/metric-burstiness/          | Good first issue                        |
| Velocity           | What is the development speed for an organization?                                                                                        | https://chaoss.community/kb/metric-project-velocity/    | Good first issue                        |
| Self-merge rates   | What is the rate of self-merges in a project?                                                                                             | https://chaoss.community/kb/metric-self-merge-rates/    | Requires more indexing of PR threads    |
| Issue Reponse Time | How much time passes between the opening of an issue and a response in the issue thread from another contributor?                         | https://chaoss.community/kb/metric-issue-response-time/ | Requires more indexing of issue threads |

### Project Metadata

Metrics that capture relevant metadata about the licensing and open sourciness of a project.

| Impact Metric         | Description                                                                    | Inspiration                                               | Comments                                |
| :-------------------- | :----------------------------------------------------------------------------- | :-------------------------------------------------------- | :-------------------------------------- |
| License Coverage      | How much of the code base has declared licenses?                               | https://chaoss.community/kb/metric-license-coverage/      | Requires more indexing of repo metadata |
| OSI Approved Licenses | What percentage of a project’s licenses are OSI approved open source licenses? | https://chaoss.community/kb/metric-osi-approved-licenses/ | Requires more indexing of repo metadata |
| Drips Access          | Does the project have a `funding.json` file?                                   | https://docs.drips.network/claim-your-repository          | Requires more indexing of repo metadata |

### Onchain Reputation

Metrics that attempt to differentiate onchain users based on behavior and trust scores.

| Impact Metric    | Description                                           | Inspiration                                                                      | Comments                                   |
| :--------------- | :---------------------------------------------------- | :------------------------------------------------------------------------------- | :----------------------------------------- |
| ENS History      | Does the user have a rich profile on ENS?             | https://app.ens.domains/                                                         | Requires indexing of ENS data              |
| Gitcoin Passport | Does the user have a high Gitcoin passport score?     | https://gitcoin.co/passport                                                      | Requires indexing of Gitcoin Passport data |
| Onchain Activity | How active is the user onchain?                       | https://docs.opensource.observer/docs/how-oso-works/impact-metrics/onchain_users | Good first issue                           |
| Network Loyalty  | How much of a user's activity is on a single network? | tbd                                                                              | Good first issue                           |
| User Segment     | What kind of dapps is the user most interested in?    | tbd                                                                              | Good first issue                           |

### Contributor Reputation

Metrics that attempt to differentiate code contributors based on behavior and PageRank-style scoring.

| Impact Metric             | Description                                                                       | Inspiration                                         | Comments                                            |
| :------------------------ | :-------------------------------------------------------------------------------- | :-------------------------------------------------- | :-------------------------------------------------- |
| Conversion Rate           | What are the rates at which new contributors become more sustained contributors?  | https://chaoss.community/kb/metric-conversion-rate/ | Good first issue                                    |
| MVPR                      | What is the most valuable pull request?                                           | tbd                                                 | Requires more indexing of related GitHub event data |
| Contributor Concentration | How much of a contributor's activity is on a single project?                      | tbd                                                 | Good first issue                                    |
| Maintainer Score          | What characteristics of a contributor's activity make them a reliable maintainer? | tbd                                                 | Good first issue                                    |
| PageRank                  | What is the PageRank of a contributor? Choose your own implementation!            | tbd                                                 | Good first issue                                    |

### Ecosystem Impact

Metrics that capture the impact of a project on the broader health of an open source ecosystem, ie, as a "talent feeder" or "dependency" for other projects.

| Impact Metric         | Description                                                                                 | Inspiration | Comments         |
| :-------------------- | :------------------------------------------------------------------------------------------ | :---------- | :--------------- |
| Contributor Feeder    | How many contributors has the project onboarded that go on to contribute to other projects? | tbd         | Good first issue |
| User Feeder           | How many omchain users has the project onboarded that go on to use other projects?          | tbd         | Good first issue |
| Elephant Factor       | How many projects depend on this project?                                                   | tbd         | Good first issue |
| Downstream Fees       | How much in sequencer fees are contributed by projects that are dependents of this project? | tbd         | Good first issue |
| Downstream Users      | How many onchain users are using this project as a dependency?                              | tbd         | Good first issue |
| Downstream Developers | How many developers are using this project as a dependency?                                 | tbd         | Good first issue |
| Network Centrality    | How central is this project to the network?                                                 | tbd         | Good first issue |

### Domain-specific Onchain Impact

Metrics that are relevant only to a specific domain, such as "defi" or "consumer", for onchain projects.

The first step in this process is to define a domain and create a list of projects that are relevant to that domain. We're currently working on this process and will be sharing more details soon. Then, any of the above metrics (as well as our existing onchain impact metrics) can be applied to the projects in that domain.

This is a good first issue for people with domain expertise who are able to curate a list of projects relevant to a specific domain.
