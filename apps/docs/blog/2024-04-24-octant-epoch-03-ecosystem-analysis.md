---
slug: octant-epoch-03-ecosystem-analysis
title: Trends and progress among OSS projects in Octant's latest epoch
authors: [ccerv1]
tags: [octant, ecosystem reports, open source]
image: https://site-assets.plasmic.app/75a76e63b052ad2cf61265abb50d3f6e.png
---

Octant recently kicked off **Epoch 3**, its latest reward allocation round, featuring [30 projects](https://octant.app/projects). This round comes three months after Epoch 2, which had a total of 24 projects in it. There are 19 projects continuing on from Epoch 2 into Epoch 3 - including [Open Source Observer](https://octant.app/project/3/0x87fEEd6162CB7dFe6B62F64366742349bF4D1B05).

During the last round, we published ["A snapshot of the 20+ open source software projects in Octant's Epoch 2"](https://docs.opensource.observer/blog/octant-epoch-02-ecosystem-analysis). In this post, we'll refresh that analysis and provide some new insights for the open source software (OSS) projects present in the current cohort.

In Epoch 3, Octant is helping support:

- 26 (out of 30) projects with at least some recent OSS component to their work
- 343 GitHub repos with regular activity
- 651 developers making regular code commits or reviews

In the last 6 months, these 26 projects:

- Attracted 881 first-time contributors
- Closed over 4,646 issues (and created 4,856 new ones)
- Merged over 9,745 pull requests (and opened 11,534 new ones)

<!-- truncate -->

## New OSS projects

Epoch 3 has a new cohort of popular, well-established OSS projects. [web3.js](https://octant.app/project/3/0x4C6fd545fc18C6538eC304Ae549717CA58f0D6eb) is one of the leading developer libraries for crypto apps. It has a massive contributor community and more than [80,000 other repos](https://packages.ecosyste.ms/registries/npmjs.org/packages/web3) import its npm package. We also have [web3.py](https://octant.app/project/3/0x5597cD8d55D2Db56b10FF4F8fe69C8922BF6C537), a library for Python developers, one that I personally use frequently (thank you!), and a dependency for [4,000 other repos](https://packages.ecosyste.ms/registries/pypi.org/packages/web3).

:::info
OSO is onboarding [ecosyste.ms](https://ecosyste.ms/) dependency data right now!
:::

The [Ethereum Attestation Service](https://octant.app/project/3/0xBCA48834b3653ec795411EB0FCBE4038F8527d62) is another OSS project conceived of many years ago but reinvigorated more recently. It has a lean team but a fast-growing contributor community and presence across various EVM chains. [Gardens (fka 1Hive)](https://octant.app/project/3/0x809C9f8dd8CA93A41c3adca4972Fa234C28F7714) is another long-standing project with a large footprint of OSS code (more than 100 repos!). It's recent activity has been focused on releasing a Gardens v2. [MetaGov](https://octant.app/project/3/0x9be7267002CAD0b8501f7322d50612CB13788Bcf) is a community laboratory that conducts peer-reviewed research and develops technical standards for emerging technology. It's been steadily building since 2019.

The three younger OSS projects that are new to Epoch 3 are all in the sweet spot for Octant's support: small teams, shipping fast. [growthepie](https://octant.app/project/3/0x9438b8B447179740cD97869997a2FCc9b4AA63a2) is a newer data platform as a public good. Check out their real-time charts including [this one](https://www.growthepie.xyz/fundamentals/profit) showing L2 onchain profits. It's quickly become a go-to source of market information for data nerds (like me), and they are expanding their impact via a new project called the [Open Labels Initiative](https://github.com/openlabelsinitiative). [NiceNode](https://octant.app/project/3/0x9cce47E9cF12C6147c9844adBB81fE85880c4df4) is a simple, open source, desktop app that does exactly what it sounds like: runs a nice node for you. The project has been around for at least 2 years, but its contributor community has doubled over the past 6 months. [StateOfEth (by Ether Alpha)](https://octant.app/project/3/0x0194325BF525Be0D4fBB0856894cEd74Da3B8356) monitors potential attack vectors on Ethereum, including centralization risks, and does outreach to rally the community when needed. The maintainer, Ether Alpha, hosts a bunch of projects on its GitHub and has had a flurry of activity (over 10K commits) in the last 6 months.

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

[Funding the Commons](https://octant.app/project/3/0x576edCed7475D8F64a5e2D5227c93Ca57d7f5d20/) is a returning project that acts as a generator function for all sorts of OSS projects and collaboration among projects. For instance, in April, FtC hosted a conference in Berkeley, California all about funding open source software - with representation from a number of the projects in Epoch 3 (Tor, growthepie, Drips, Hypercerts, Gitcoin, MetaGov, Open Source Observer...)

[Boring Security](https://octant.app/project/3/0x52C45Bab6d0827F44a973899666D9Cd18Fd90bCF) is another project supporting the OSS community and Ethereum users, but more through its security-related efforts than through its code contributions. There are also two new, non-OSS projects - [ETH Daily](https://octant.app/project/3/0xEB40A065854bd90126A4E697aeA0976BA51b2eE7) and [RefiDAO](https://octant.app/project/3/0x7340F1a1e4e38F43d2FCC85cdb2b764de36B40c0) - joining the Epoch. Both are well-known fixtures in the Ethereum grantmaking community. ETH Daily provides a _daily_ podcast and newsletter to a community of 2000+ subscribers. RefiDAO is a podcast, eventmaker, and DAO of DAOs ("local nodes") working on regenerative finance and other real world use cases. Check them out!

## Returning OSS projects

We won't go into detail of every returning project, but here are some high level metrics for the 18 OSS projects in Epoch 3 that we also covered in Epoch 2.

<p style={{fontSize: 'small'}}>

| Project                                         | Drips | EthStaker | Ethereum Cat Herders | Gitcoin | Giveth | Glo Dollar | Hypercerts | L2BEAT | MetaGame | NiceNode | Open Source Observer | Pairwise | Praise | Protocol Guild | Revoke | Shutter Network | The Tor Project | rotki |
| :---------------------------------------------- | ----: | --------: | -------------------: | ------: | -----: | ---------: | ---------: | -----: | -------: | -------: | -------------------: | -------: | -----: | -------------: | -----: | --------------: | --------------: | ----: |
| Active Repos - Last 6 Months                    |     9 |         6 |                    1 |      47 |     22 |          2 |         10 |      8 |        8 |       11 |                    5 |        5 |      5 |             92 |      6 |              15 |              13 |    17 |
| Fork Count - Max of Active Repos                |    17 |       187 |                 5040 |     422 |     31 |          1 |         24 |    329 |       76 |       26 |                   22 |        0 |     19 |          19417 |    208 |              14 |             926 |   475 |
| Star Count - Max of Active Repos                |    58 |       426 |                12523 |     886 |     30 |          3 |         81 |    457 |      127 |      168 |                   37 |        7 |     32 |          46063 |    620 |              57 |            4304 |  2609 |
| Commit Code - All Repos, Last 6 Months          |   382 |       430 |                  270 |    2877 |   2708 |         62 |        362 |    754 |      255 |      255 |                  678 |      330 |     24 |          11167 |    312 |             251 |             428 |  1937 |
| Issue Closed - All Repos, Last 6 Months         |   137 |        46 |                   31 |     925 |    710 |          0 |        197 |     39 |       58 |       18 |                  332 |       89 |      0 |           1390 |     69 |               6 |               7 |   168 |
| Issue Created - All Repos, Last 6 Months        |   148 |        54 |                   59 |    1007 |    563 |          2 |        132 |     34 |       35 |       35 |                  437 |      128 |      0 |           1528 |     67 |              16 |              15 |   188 |
| Pull Request Created - All Repos, Last 6 Months |   173 |       277 |                  393 |    1102 |    612 |          6 |        192 |   1390 |       80 |      161 |                  505 |       76 |      3 |           4684 |     44 |              52 |              11 |  1111 |
| Pull Request Merged - All Repos, Last 6 Months  |   160 |       276 |                  252 |     977 |    566 |          4 |        175 |   1255 |       61 |      121 |                  482 |       73 |      4 |           3688 |     43 |              42 |               2 |  1073 |
| Total Contributors - All Time                   |    38 |       228 |                 1515 |    1807 |    314 |          8 |         25 |    276 |      145 |       23 |                   30 |       15 |     29 |          14721 |    162 |              22 |             741 |   493 |
| New Contributors - Last 6 Months                |    13 |        40 |                  129 |      67 |      9 |          0 |          9 |     95 |        2 |       11 |                   25 |        6 |      0 |            890 |     66 |               6 |              26 |    62 |
| Total Developers - Avg Last 6 Months            |   3.8 |       4.7 |                  2.8 |      17 |    9.7 |          1 |        2.7 |   12.5 |      3.2 |      1.3 |                  4.3 |      2.2 |    0.3 |           60.7 |      1 |             3.5 |             1.8 |   5.3 |

</p>

## Make your allocations

Like past iterations, the signal-to-noise ratio is very high among projects on the Octant app. The deadline to allocate rewards to these projects is 30 April 2024. If you're a staker, go allocate now! To allocate or find more information about the current set of projects, check out the [Octant App](https://octant.app/projects).

If you are interested in contributing to analysis like this, we invite you to join [our data collective](https://opensource.observer/data-collective). You can also view the queries and analysis Notebook behind this and other Octant reports [here](https://github.com/opensource-observer/insights/tree/main/analysis/octant).
