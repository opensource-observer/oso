---
slug: octant-epoch-03-ecosystem-analysis
title: Trends and progress among OSS projects in Octant's latest epoch
authors: [ccerv1]
tags: [octant, data science, ecosystem reports, open source]
image: https://site-assets.plasmic.app/75a76e63b052ad2cf61265abb50d3f6e.png
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

Octant recently kicked off **Epoch 3**, its latest reward allocation round, featuring [30 projects](https://octant.app/projects). This round comes three months after Epoch 2, which had a total of 24 projects in it. There are 20 projects continuing on from Epoch 2 into Epoch 3 - including [Open Source Observer](https://octant.app/project/3/0x87fEEd6162CB7dFe6B62F64366742349bF4D1B05).

During Epoch 2, we published a [blog post](./2024-01-26-octant-epoch-02-ecosystem-analysis.mdx) with some high-level indicators about the 20+ open source software (OSS) projects participating in the round. In this post, we'll provide some insights about the new OSS projects and refresh our analysis for the returning projects.

Overall, in Epoch 3, Octant is helping support:

- 26 (out of 30) projects with at least some recent OSS component to their work
- 343 GitHub repos with regular activity
- 651 developers making regular code commits or reviews

In the last 6 months, these 26 projects:

- Attracted 881 first-time contributors
- Closed over 4,646 issues (and created 4,856 new ones)
- Merged over 9,745 pull requests (and opened 11,534 new ones)

<!-- truncate -->

## New OSS projects

Epoch 3 has a new cohort of popular, well-established OSS projects.

[web3.js](https://octant.app/project/3/0x4C6fd545fc18C6538eC304Ae549717CA58f0D6eb) is one of the leading developer libraries for crypto apps. It has a massive contributor community and more than [80,000 other repos](https://packages.ecosyste.ms/registries/npmjs.org/packages/web3) rely on its npm package. Epoch 3 also includes [web3.py](https://octant.app/project/3/0x5597cD8d55D2Db56b10FF4F8fe69C8922BF6C537), a popular library for Python developers, which is housed in the `ethereum` GitHub org space and is a dependency for [4,000 other repos](https://packages.ecosyste.ms/registries/pypi.org/packages/web3). _PSA: OSO is in the process of onboarding [ecosyste.ms](https://ecosyste.ms/) dependency data right now._

The [Ethereum Attestation Service](https://octant.app/project/3/0xBCA48834b3653ec795411EB0FCBE4038F8527d62) is another foundational OSS project participating in the round. It has a lean team but a fast-growing contributor community and presence across various EVM chains. [Gardens (fka 1Hive)](https://octant.app/project/3/0x809C9f8dd8CA93A41c3adca4972Fa234C28F7714) is a long-standing project with a large footprint of OSS code (more than 100 repos!). Its recent activity has been focused on releasing a Gardens v2. [MetaGov](https://octant.app/project/3/0x9be7267002CAD0b8501f7322d50612CB13788Bcf) is a community laboratory that conducts peer-reviewed research and develops technical standards for emerging technology. It's been steadily building since 2019.

There are also three younger OSS projects that are new to Epoch 3 but are in the sweet spot for Octant's support: small teams, shipping fast. [growthepie](https://octant.app/project/3/0x9438b8B447179740cD97869997a2FCc9b4AA63a2) is a data platform as a public good, with excellent real-time charts, such as [this one](https://www.growthepie.xyz/fundamentals/profit) showing L2 onchain profits. They are expanding their impact via a new project called the [Open Labels Initiative](https://github.com/openlabelsinitiative). [NiceNode](https://octant.app/project/3/0x9cce47E9cF12C6147c9844adBB81fE85880c4df4) is a simple, open source, desktop app that does exactly what it sounds like: runs a nice node for you. The project has been around for at least two years, but its contributor community has doubled over the past 6 months. [StateOfEth (by Ether Alpha)](https://octant.app/project/3/0x0194325BF525Be0D4fBB0856894cEd74Da3B8356) monitors potential attack vectors on Ethereum, including centralization risks, and does outreach to rally the community when needed. The maintainer, Ether Alpha, hosts a bunch of projects on its GitHub and has had a flurry of activity (over 10K commits) in the last 6 months.

<Tabs>
  <TabItem value="summary" label="Summary" default>
    <p style={{fontSize: 'small'}}>
    | Project                      |   Active Repos - Last 6 Months |   Fork Count - Max of Active Repos |   Star Count - Max of Active Repos |
    |:-----------------------------|-------------------------------:|-----------------------------------:|-----------------------------------:|
    | 1Hive Gardens                |                              9 |                                 37 |                                 28 |
    | StateOfEth (by Ether Alpha)  |                             13 |                                 21 |                                 22 |
    | Ethereum Attestation Service |                              8 |                                 55 |                                213 |
    | growthepie                   |                              4 |                                  5 |                                 13 |
    | MetaGov                      |                             21 |                                 20 |                                 72 |
    | web3.js                      |                              5 |                               4831 |                              18764 |
    | web3.py                      |                              1 |                               1620 |                               4790 |
    </p>
  </TabItem>
  <TabItem value="contribs" label="Contributors">
    <p style={{fontSize: 'small'}}>
    | Project                      |   Total Contributors - All Time |   New Contributors - Last 6 Months |   Full-time Developers - Avg Last 6 Months |   Total Developers - Avg Last 6 Months |
    |:-----------------------------|--------------------------------:|-----------------------------------:|-------------------------------------------:|---------------------------------------:|
    | 1Hive Gardens                |                             326 |                                  2 |                                        0   |                                    2.2 |
    | StateOfEth (by Ether Alpha)  |                              35 |                                  3 |                                        1.3 |                                    2.2 |
    | Ethereum Attestation Service |                              82 |                                 43 |                                        0   |                                    2   |
    | growthepie                   |                               8 |                                  2 |                                        1.2 |                                    4   |
    | MetaGov                      |                              65 |                                  3 |                                        0   |                                    5.2 |
    | web3.js                      |                            2308 |                                112 |                                        0.2 |                                    5.2 |
    | web3.py                      |                             949 |                                 56 |                                        0   |                                    4.2 |
    </p>
  </TabItem>
  <TabItem value="activity" label="Activity">
    <p style={{fontSize: 'small'}}>
    | Project                      |   Commit Code - All Repos, Last 6 Months |   Issue Closed - All Repos, Last 6 Months |   Issue Created - All Repos, Last 6 Months |   Pull Request Created - All Repos, Last 6 Months |   Pull Request Merged - All Repos, Last 6 Months |
    |:-----------------------------|-----------------------------------------:|------------------------------------------:|-------------------------------------------:|--------------------------------------------------:|-------------------------------------------------:|
    | 1Hive Gardens                |                                      139 |                                        42 |                                         65 |                                                88 |                                               67 |
    | StateOfEth (by Ether Alpha)  |                                    16217 |                                         1 |                                          1 |                                                12 |                                                8 |
    | Ethereum Attestation Service |                                      275 |                                        20 |                                         24 |                                                75 |                                               42 |
    | growthepie                   |                                     1025 |                                         1 |                                          0 |                                                56 |                                               54 |
    | MetaGov                      |                                      417 |                                        20 |                                         31 |                                                45 |                                               43 |
    | web3.js                      |                                      184 |                                       203 |                                        222 |                                               217 |                                              156 |
    | web3.py                      |                                      243 |                                       137 |                                         65 |                                               148 |                                              121 |
    </p>
  </TabItem>
</Tabs>

## Non-OSS projects

[Funding the Commons](https://octant.app/project/3/0x576edCed7475D8F64a5e2D5227c93Ca57d7f5d20/) is a returning project that acts as a generator function for all sorts of OSS projects and collaboration among projects. For instance, in April, FtC hosted a conference in Berkeley, California focused on funding open source software. There was representation from a number of the projects in Epoch 3, including Tor, growthepie, Drips, Hypercerts, Gitcoin, MetaGov, and Open Source Observer.

[Boring Security](https://octant.app/project/3/0x52C45Bab6d0827F44a973899666D9Cd18Fd90bCF) is another project supporting the OSS community and Ethereum users, but more through its security-related efforts than through its code contributions. There are also two new, non-OSS projects - [ETH Daily](https://octant.app/project/3/0xEB40A065854bd90126A4E697aeA0976BA51b2eE7) and [RefiDAO](https://octant.app/project/3/0x7340F1a1e4e38F43d2FCC85cdb2b764de36B40c0) - joining the Epoch. Both are well-known fixtures in the Ethereum grantmaking community. ETH Daily provides a _daily_ podcast and newsletter to a community of 2000+ subscribers. RefiDAO is a podcast, eventmaker, and DAO of DAOs ("local nodes") working on regenerative finance and other real world use cases. Check them out!

## Returning OSS projects

We won't go into detail of every returning project, but here are some high level metrics for the 18 OSS projects in Epoch 3 that we also covered in Epoch 2.

<Tabs>
  <TabItem value="summary" label="Summary" default>
    <p style={{fontSize: 'small'}}>
    | Project                              |   Active Repos - Last 6 Months |   Fork Count - Max of Active Repos |   Star Count - Max of Active Repos |
    |:-------------------------------------|-------------------------------:|-----------------------------------:|-----------------------------------:|
    | Drips                                |                              9 |                                 17 |                                 58 |
    | Ethereum Cat Herders                 |                              1 |                               5040 |                              12523 |
    | EthStaker                            |                              6 |                                187 |                                426 |
    | Gitcoin                              |                             47 |                                422 |                                886 |
    | Giveth                               |                             22 |                                 31 |                                 30 |
    | Glo Dollar                           |                              2 |                                  1 |                                  3 |
    | Hypercerts                           |                             10 |                                 24 |                                 81 |
    | L2BEAT                               |                              8 |                                329 |                                457 |
    | MetaGame                             |                              8 |                                 76 |                                127 |
    | NiceNode                             |                             11 |                                 26 |                                168 |
    | Open Source Observer                 |                              5 |                                 22 |                                 37 |
    | Pairwise                             |                              5 |                                  0 |                                  7 |
    | Praise                               |                              5 |                                 19 |                                 32 |
    | Protocol Guild                       |                             92 |                              19417 |                              46063 |
    | Revoke                               |                              6 |                                208 |                                620 |
    | rotki                                |                             17 |                                475 |                               2609 |
    | Shielded Voting (by Shutter Network) |                             15 |                                 14 |                                 57 |
    | The Tor Project                      |                             13 |                                926 |                               4304 |
    </p>
  </TabItem>
  <TabItem value="contribs" label="Contributors">
    <p style={{fontSize: 'small'}}>
    | Project                              |   Total Contributors - All Time |   New Contributors - Last 6 Months |   Full-time Developers - Avg Last 6 Months |   Total Developers - Avg Last 6 Months |
    |:-------------------------------------|--------------------------------:|-----------------------------------:|-------------------------------------------:|---------------------------------------:|
    | Drips                                |                              38 |                                 13 |                                        1   |                                    3.8 |
    | Ethereum Cat Herders                 |                            1515 |                                129 |                                        1   |                                    2.8 |
    | EthStaker                            |                             228 |                                 40 |                                        1   |                                    4.7 |
    | Gitcoin                              |                            1807 |                                 67 |                                        5   |                                   17   |
    | Giveth                               |                             314 |                                  9 |                                        1.7 |                                    9.7 |
    | Glo Dollar                           |                               8 |                                  0 |                                        0   |                                    1   |
    | Hypercerts                           |                              25 |                                  9 |                                        0.3 |                                    2.7 |
    | L2BEAT                               |                             276 |                                 95 |                                        1.5 |                                   12.5 |
    | MetaGame                             |                             145 |                                  2 |                                        0.3 |                                    3.2 |
    | NiceNode                             |                              23 |                                 11 |                                        0.8 |                                    1.3 |
    | Open Source Observer                 |                              30 |                                 25 |                                        1.8 |                                    4.3 |
    | Pairwise                             |                              15 |                                  6 |                                        0.2 |                                    2.2 |
    | Praise                               |                              29 |                                  0 |                                        0   |                                    0.3 |
    | Protocol Guild                       |                           14721 |                                890 |                                       11.3 |                                   60.7 |
    | Revoke                               |                             162 |                                 66 |                                        0.8 |                                    1   |
    | rotki                                |                             493 |                                 62 |                                        3.3 |                                    5.3 |
    | Shielded Voting (by Shutter Network) |                              22 |                                  6 |                                        0   |                                    3.5 |
    | The Tor Project                      |                             741 |                                 26 |                                        0.8 |                                    1.8 |
    </p>
  </TabItem>
  <TabItem value="activity" label="Activity">
    <p style={{fontSize: 'small'}}>
    | Project                              |   Commit Code - All Repos, Last 6 Months |   Issue Closed - All Repos, Last 6 Months |   Issue Created - All Repos, Last 6 Months |   Pull Request Created - All Repos, Last 6 Months |   Pull Request Merged - All Repos, Last 6 Months |
    |:-------------------------------------|-----------------------------------------:|------------------------------------------:|-------------------------------------------:|--------------------------------------------------:|-------------------------------------------------:|
    | Drips                                |                                      382 |                                       137 |                                        148 |                                               173 |                                              160 |
    | Ethereum Cat Herders                 |                                      270 |                                        31 |                                         59 |                                               393 |                                              252 |
    | EthStaker                            |                                      430 |                                        46 |                                         54 |                                               277 |                                              276 |
    | Gitcoin                              |                                     2877 |                                       925 |                                       1007 |                                              1102 |                                              977 |
    | Giveth                               |                                     2708 |                                       710 |                                        563 |                                               612 |                                              566 |
    | Glo Dollar                           |                                       62 |                                         0 |                                          2 |                                                 6 |                                                4 |
    | Hypercerts                           |                                      362 |                                       197 |                                        132 |                                               192 |                                              175 |
    | L2BEAT                               |                                      754 |                                        39 |                                         34 |                                              1390 |                                             1255 |
    | MetaGame                             |                                      255 |                                        58 |                                         35 |                                                80 |                                               61 |
    | NiceNode                             |                                      255 |                                        18 |                                         35 |                                               161 |                                              121 |
    | Open Source Observer                 |                                      678 |                                       332 |                                        437 |                                               505 |                                              482 |
    | Pairwise                             |                                      330 |                                        89 |                                        128 |                                                76 |                                               73 |
    | Praise                               |                                       24 |                                         0 |                                          0 |                                                 3 |                                                4 |
    | Protocol Guild                       |                                    11167 |                                      1390 |                                       1528 |                                              4684 |                                             3688 |
    | Revoke                               |                                      312 |                                        69 |                                         67 |                                                44 |                                               43 |
    | rotki                                |                                     1937 |                                       168 |                                        188 |                                              1111 |                                             1073 |
    | Shielded Voting (by Shutter Network) |                                      251 |                                         6 |                                         16 |                                                52 |                                               42 |
    | The Tor Project                      |                                      428 |                                         7 |                                         15 |                                                11 |                                                2 |
    </p>
  </TabItem>
</Tabs>

## Make your allocations

Like past iterations, the signal-to-noise ratio is very high among projects on the Octant app. The deadline to allocate rewards to these projects is 30 April 2024. If you're a staker, go allocate now! To allocate or find more information about the current set of projects, check out the [Octant App](https://octant.app/projects).

If you are interested in contributing to analysis like this, we invite you to join [our data collective](https://opensource.observer/data-collective). You can also view the queries and analysis Notebook behind this and other Octant reports [here](https://github.com/opensource-observer/insights/tree/main/analysis/octant).
