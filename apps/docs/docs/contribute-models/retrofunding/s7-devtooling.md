---
title: "S7: Developer Tooling"
sidebar_position: 2
---

:::warning
This document is a work in progress, with placeholders in some of the important sections currently under development.
:::

This document explains how the **Retro Funding S7: Developer Tooling Mission** will evaluate project-level impact.

The methodology considers onchain usage, developer engagement, and direct dependencies and creates a graph to score open source devtooling projects using OpenRank's implementation of the [EigenTrust algorithm](https://docs.openrank.com/reputation-algorithms/eigentrust). We then propose **three impact evaluation algorithms** by asssigning different weights and other parameters to the graph.

Please note: This is the first in a series of evaluations we will be making over the next few months. Your feedback and contributions are welcome!

## Context

In 2025, Optimism’s Retro Funding (RF) program is shifting to a "metrics-driven, humans-in-the-loop" approach. We present various strategies for scoring projects; citizens vote on the algorithms they like best. This particular round—**Retro Funding S7: Developer Tooling**—focuses on open source compilers, libraries, debuggers, and other toolchains that help builders to create interop-compatible apps on the Superchain. For the complete round details, see [here](https://gov.optimism.io/t/retro-funding-dev-tooling-mission-details/9598).

### Expected Impact

The overall goals for this round include:

- Grow the number and variety of dev toolchains supporting cross-chain or interoperable features.
- Expand the Superchain developer community and create network effects around using and contributing toopen source tooling.
- Demonstrate a tangible lift in cross-chain or onchain activity resulting from robust tools.

Remember, we are not trying to _predict_ which projects will continue to have the most impact in the future. Instead, we are trying to reward projects that have already had demonstrable impact.

### Scope

We can estimate the current size of the devtooling ecosystem by looking at the number of packages being imported by onchain builder projects.

- A total of X projects with deployments on the Superchain were included in OSO's dataset prior to the start of the round.
- These projects have a total of Y distinct packages in their dependency graphs:
  - JavaScript/TypeScript (via npm): Z
  - Rust (via crates): A
  - Python (via pypi): B
  - Other: C
- Many of these are standard web2 dependencies, but a total of X can be linked to Y projects that have applied for Retro Funding in past rounds.
- Excluding self-edges (i.e., projects that import their own packages), we can estimate the total number of devtooling links to be X and the number of links between onchain builders and Retro Funded-projects to be Z.

We can also estimate the number of active developers contributing to onchain builder projects.

- From the same X projects, we can estimate that a total of X developers made one or more commits to an onchain builder project in the past 6 months.
- Applying a higher activity threshold (at least three months of activity over the past 6 months to a repo in Solidity, Vyper, TypeScript, or Rust), we estimate a total of Y distinct developers.
- These developers have a total of Y distinct GitHub accounts.

## Evaluation Methodology

The evaluation is powered by Open Source Observer’s pipeline, which:

1. **Collects** onchain project data (transactions, users, etc.), package dependencies (npm, crates, etc.), and developer events (commits, PRs, forks, etc.).
2. **Builds** a directed graph from Onchain Projects → Developers → Devtooling Projects.
3. **Seeds** adds trust scores in three ways:
   - Onchain projects get pretrust for their economic activity (e.g., transaction volume).
   - Devtooling projects get pretrust for their GitHub signals (e.g., number of packages published).
   - Developers get reputation from the onchain projects they contribute to and give reputation to devtooling projects they engage with via GitHub events.
4. **Runs** an [OpenRank-based](https://docs.openrank.com/) algorithm ([EigenTrust](https://nlp.stanford.edu/pubs/eigentrust.pdf)) on the weighted graph to compute final scores for devtooling projects.
5. **Normalizes** applies a set of normalization functions to the scores and ensures they are within the min/max reward caps for the round.

To view the full lineage and sample results for each algorithm, see the [DevtoolingCalculator](https://app.hex.tech/00bffd76-9d33-4243-8e7e-9add359f25c7/app/d5da455e-b49a-47d6-a88d-dce1f679a02b/latest).

### Eligibility

Projects must meet the following criteria in order to be eligible for rewards:

1. **Open Source**: Be actively maintained and have a public GitHub repository with a history of public commits; and
2. **Packages**: Be included in the dependency graph of at least **three** qualified onchain builder projects; or
3. **Developer Engagement**: Be included in the GitHub engagement graph by at least **ten** developers who are active contributors to onchain builder projects (e.g., commits, issues, pull requests, stars, forks, etc.).

<details>
<summary>What are the requirements to be considered open source?</summary>

A project is considered open source if it meets the following criteria:

- Currently, has a public GitHub repository.
- Has a history of public GitHub activity at least one month before the start of the round.
- Has recent public GitHub activity (multiple commits) within the past 6 months.

Note: We do not consider any activity made during periods when a repo was private. This is both a design choice and a technical limitation. OSO's GitHub data source ([gharchive](https://docs.opensource.observer/docs/integrate/datasets/#github-archive)) does not backfill private repo activity.

</details>

<details>
<summary>What's a qualified onchain builder?</summary>

Qualified onchain builder projects are those that have:

- Verified their GitHub and contract ownership on OP Atlas.
- Contributed 0.01 ETH in L2 gas fees (across the Superchain) within the past 6 months.

</details>

<details>
<summary>What types of package links are considered?</summary>

The software supply chain is complex and we are currently unable to consider all possible package links. To be considered, a package must:

- Be published in a public registry (e.g., npm, crates, pypi). Note: we have some support for Go package links hosted on GitHub.
- Link to the devtooling project's public repository in the package metadata. This is a standard best practice in the industry.
- Be included in the GitHub [SBOMs](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/exporting-a-software-bill-of-materials-for-your-repository) of qualified onchain builder projects.

We have plans to expand our support for other types of package links in the future. See below for more details.

</details>

<details>
<summary>What counts as developer engagement?</summary>

OSO tracks all forms of developer engagement with a repo (e.g., commits, PRs, issues, stars, forks, comments, etc.). However, we do not weight all forms of engagement equally. The following variables are used to weight engagement types:

- The developer who made the event and their reputation. Engagement from high-reputation developers is generally weighted more heavily.
- The type of event (e.g., commit, PR, issue, star, fork, comment). Certain events are considered more impactful than others (e.g., commit > star).
- When the event occurred. In some models, events that occurred more recently are weighted more heavily.

The exact weights and decay rates are algorithm-specific.

</details>

### Graph Construction

We build a directed trust graph that ties onchain projects, developers, and devtooling projects together:

1. **Onchain Projects → Devtooling Projects**

   We draw edges from onchain projects to devtooling projects whenever an onchain repo imports a package maintained by a devtooling project. This is based on data from the [SBOMs](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/exporting-a-software-bill-of-materials-for-your-repository) of qualified onchain builder projects. These links are timestamped based on the last time OSO ran its SBOM indexer (typically weekly).

   We currently count each relationship between an onchain project and a devtooling project as a single edge, even if the onchain project has multiple dependencies on the devtooling project. This is an important trade-off designed to reduce the incentive for devtooling projects to split their code into multiple packages to potentially game the system.

2. **Onchain Projects → Developers**

   We define an edge from an onchain project to a developer whenever a developer has made one or more commits to an onchain builder project. Developer activity is aggregated at the project (not repo level), meaning that there is no difference between a developer who worked on a single repo or multiple repos. These links are bucketed by month, so there is no difference between a developer who made a single commit versus 100 commits in a month.

   If an onchain project has multiple active developers, we count each developer as a separate edge. The trust that flows from an onchain project to a developer is a function of how many active developers the onchain project has.

3. **Developers → Devtooling Projects**

   We define an edge from a developer to a devtooling project whenever a developer has engaged (i.e., via commits, opening a PR or issue, starring, forking, commenting in a PR or issue thread, etc.) with a devtooling project. These forms of developer activity are also aggregated at the project (not repo level), meaning that there is no difference between a developer who starred a single repo vs all of a devtooling project's repos. These links are bucketed by month, so there is no difference between a developer who opened a single PR versus 100 PRs in a month.

All edges are directed. Onchain projects pass trust to developers and devtooling projects (via package dependencies), and developers pass additional trust to devtooling projects (via GitHub events).

<details>
<summary>What about historical dependencies?</summary>

We have plans to include historical dependency data in future iterations of the evaluation. Currently, however, our metrics are only on the latest dependency data.

</details>

<details>
<summary>What about self-loops?</summary>

If a developer’s own project is also recognized as an onchain project, the pipeline removes self-loop duplicates. This prevents artificially amplifying trust for projects that act as both an onchain builder and a devtooling library under the same entity.

</details>

<details>
<summary>Which types of packages are considered?</summary>

We primarly consider npm (JavaScript/TypeScript), crates (Rust), and pypi (Python) package links. We have some support for Go package links hosted on GitHub, although Go is generally not as relevant to the app-side of the onchain builder ecosystem.

We recognize that this is not a comprehensive list of all possible package links and dependencies.

In the future, we hope to include [git submodules](https://github.blog/open-source/git/working-with-submodules/) and GitHub Actions as a source of package links.

We are also open to adding more crypto-specific package managers (e.g., Soldeer) in the future.

</details>

<details>
<summary>What about other ways of reusing code?</summary>

Other ways of reusing code, such as developing off a fork or a clone, or directly copying code, are not currently considered. In general, our assumption is that network effects will accrue around projects that are viewed as most legitimate by the community.

As this is only a first iteration of the devtooling evaluation, we are curious to see examples of projects that have their impact diluted by these alternative code reuse mechanisms.

</details>

### Metrics

This section describes the metrics used to seed the trust graph.

Critically, these metrics are used as **pre-trust inputs** to the EigenTrust algorithm. For instance, a project that has a lot of packages but no links to onchain builder projects would receive a low score. Similarly, a project that has very few stars or forks overall but a lot of recent activity from high-reputation developers would receive a high score.

All other things being equal, a project that is a dependency for a high-impact onchain builder project will receive a higher score than a project that is a dependency for a low-impact onchain builder project.

- **Onchain Projects**

  - **Transaction volume** – The number of Superchain transactions involving one or more of the project's contracts over the past 180 days.
  - **Gas fees** – The total gas fees paid by users interacting with the project's contracts over the past 180 days.
  - **Bot-filtered user counts** – The number of distinct addresses that have interacted with the project's contracts over the past 180 days.

- **Developers**

  - **Active months** – The number of months that a developer has made commits to an onchain builder project since 2024-01-01.
  - **Language** – The primary programming language for the onchain builder repo(s) where the developer has made their commits.
  - **Engagement with devtooling projects** – The time and type of event between a developer and a devtooling project.

- **Devtooling Projects**
  - **Stars and forks** – The total number of stars and forks all repos owned by the devtooling project have received on GitHub.
  - **Package count** – The total number of distinct packages the devtooling released on major package servers (e.g., npm, crates, pypi).

One of the key parameters in the EigenTrust algorithm is the **alpha** parameter. This controls the portion of the EigenTrust output taken from the pre-trust values vs. the iterative trust propagation step.

<details>
<summary>Why these metrics?</summary>

These metrics are relatively simple to measure and widely applicable to different types of projects.

</details>

<details>
<summary>Are metrics normalized?</summary>

Yes. We apply log scaling andmin-max normalization to the pre-trust values to ensure no single dimension dominates the combined score.

</details>

<details>
<summary>What if a package is used by onchain projects that are not in OP Atlas?</summary>

For retro funding, we do not currently track onchain projects that are not in OP Atlas. OSO has a larger registry of onchain projects, so we can simulate results if the project pool is expanded or different.

</details>

### Weighting and Time Decay

Each algorithm has a different set of weights and time decay parameters.

Specifically, there are four types of settings:

- **Pretrust Weights**. These are the weights applied to the pretrust values for onchain projects, developers, and devtooling projects. For instance, an algorithm may weight transaction volume more heavily than user numbers, or the number of packages published more heavily than stars and forks.
- **Link Type Weights**. These are the weights applied to the different types of edges in the graph. For instance, an algorithm may weight package dependencies more heavily than developer engagement.
- **Event Type Weights**. These are the weights applied to the different types of events in the graph. For instance, an algorithm may weight crates installs more heavily than npm, or PRs more heavily than stars.
- **Time Decay**. This is the time decay applied to the different types of events in the graph. For instance, an algorithm may apply a stronger decay to older commits than newer ones.

<details>
<summary>How exactly does the time decay work?</summary>

The time decay is applied to the different types of events in the graph. Insert the actual formula from the code here.

</details>

<details>
<summary>Can you apply different time decays to different types of events?</summary>

This is entirely possible, but not currently implemented.

</details>

<details>
<summary>Can you penalize spammy engagement?</summary>

This is entirely possible, but not currently implemented.

</details>

### EigenTrust

Our scoring process uses [EigenTrust](https://docs.openrank.com/reputation-algorithms/eigentrust) to propagate trust through the graph until it converges to stable scores:

1. **Pretrust Seed**

   - Onchain projects start with pretrust that reflects their economic activity (transactions, fees, user counts).
   - Devtooling projects get pretrust based on GitHub popularity (stars, forks, packages published).
   - Developers receive reputation from onchain projects where they have contributed code (commits, PRs).

2. **Aggregation**

   - We unify these pretrust values into a single vector. Each onchain project, devtooling project, and developer has an initial trust weight based on the metrics described above.

3. **Propagation**

   - EigenTrust iteratively distributes trust across the graph. Nodes with high pretrust pass a portion of that trust to the nodes they point to. The algorithm converges after several iterations to a stable set of trust scores.

4. **Normalization**
   - Scores are normalized to ensure no project dominates. We also apply min-max reward caps to keep allocations fair across extremely large or small scores.

<details>
<summary>Why EigenTrust?</summary>

EigenTrust is a well-known reputation algorithm used to dampen dishonest behavior (like sybil attacks) by requiring trust to flow from established “seed” nodes. It converges quickly on large graphs and is less sensitive to outliers than naive ranking methods.  
For more details, see [this original paper](https://nlp.stanford.edu/pubs/eigentrust.pdf) and the [OpenRank EigenTrust docs](https://docs.openrank.com/openrank-sdk/sdk-references/eigentrust).

</details>

<details>
<summary>How is the alpha parameter set?</summary>

The alpha parameter is set to 0.2 by default. This means that 20% of the trust score is based on the pretrust values, and 80% is based on the iterative trust propagation step.

</details>

### Finalizing Scores

After EigenTrust converges, we rank devtooling projects by their final trust score. Projects that do not meet the basic thresholds (e.g., fewer than three onchain package dependencies or fewer than ten active developer engagements) are considered ineligible.

- **Ranking** – Devtooling projects that remain eligible are sorted by their EigenTrust score.
- **Reward Calculation** – Final reward amounts are computed by normalizing each project’s score and then distributing funds within the round’s minimum/maximum per-project caps.

---

## Proposed Algorithms

Each algorithm references a different YAML file but shares the same underlying pipeline, with distinct weights and decays.

### Arcturus

This algorithm aims to reward projects with significant current adoption. It focuses on total dependents and downstream impact—how many developers or onchain users benefit from these tools. By recognizing well-established projects that already power much of the ecosystem, Arcturus supports cornerstone infrastructure that large numbers of builders rely on.

<details>
<summary>Weightings & Sample Results</summary>

- **Onchain Pretrust**: Weighted heavily toward transaction/gas usage.
- **Devtooling Pretrust**: Some star/fork credit, but mostly focusing on dependency references.
- **Link Weights**: **5x** for `PACKAGE_DEPENDENCY` edges.
- **Time Decay**: `commit_to_onchain_repo = 1.0`, `event_to_devtooling_repo = 0.5`.

```
1. Ethers.js: https://github.com/ethers-io
2. OpenZeppelin: https://github.com/openzeppelin
3. Hardhat: https://github.com/nomicfoundation/hardhat
4. wevm: https://github.com/wevm
5. web3.js: https://github.com/web3/web3.js
```

</details>

### Bellatrix

This algorithm rewards projects that are rapidly growing in adoption and impact. It measures net gains in dependents, developer traction, and onchain usage over the past six months. By prioritizing growth metrics, it encourages new or recently revamped tools that quickly gain traction among onchain builders.

<details>
<summary>Weightings & Sample Results</summary>

- **Onchain Pretrust**: Moderately distributed, so developer connections matter more.
- **Devtooling Pretrust**: Weighted strongly by star/fork counts.
- **Link Weights**: Developer → devtooling edges get a high weight (4x).
- **Time Decay**: More rapid decay for commits to highlight **recent** dev activity.

```
1. Foundry: https://github.com/foundry-rs
2. wevm: https://github.com/wevm
3. Alloy: https://github.com/alloy-rs
4. Pyth: https://github.com/pyth-network/pyth-sdk-rs
5. whatsabi: https://github.com/shazow/whatsabi
```

</details>

### Canopus

This algorithm measures a project’s developer engagement and utility across the onchain builder ecosystem. It looks not only at dependencies but also how many trusted developers (especially those known for smart contract work) commit, open pull requests, comment on issues, star, or fork these tools. This gives projects that improve the developer experience beyond offering npm / Rust packages a more even footing.

<details>
<summary>Weightings & Sample Results</summary>

- **Onchain Pretrust**: Balanced among tx counts, gas, and user metrics.
- **Devtooling Pretrust**: Mix of popularity (stars/forks) and real dev usage.
- **Link Weights**: Emphasizes both direct usage (4x) and dev engagement (2x).
- **Time Decay**: Moderately reduces older events.

```
1. Hardhat: https://github.com/nomicfoundation/hardhat
2. Prettier Solidity: https://github.com/prettier-solidity
3. OpenZeppelin: https://github.com/openzeppelin
4. Sourcify: https://github.com/ethereum/sourcify
5. blst: https://github.com/supranational/blst
```

</details>

## Contributing

Here are ideas for improving the evaluation:

1. **Expand Data Sources**  
   Onboard additional package registries and other data about devtooling projects.
2. **Propose More Metrics**  
   Help refine our set of pretrust metrics and edges in the graph.
3. **Qualitative Feedback**  
   Compare the results of different algorithms with qualitative feedback from the community.
4. **Try Different Algorithms**  
   Fine-tune our initial algorithms with improved weights. Propose different weights and decay parameters entirely. Experiment with other algorithms (eg, PageRank, Hubs & Authorities).

## Further Resources

- [Retro Funding Algorithms Repo](https://github.com/ethereum-optimism/Retro-Funding)
- [Optimism Interop tooling docs](https://docs.optimism.io/stack/interop/tools)
- [Open Rank docs](https://docs.openrank.com/)
- [EigenTrust Paper](https://nlp.stanford.edu/pubs/eigentrust.pdf)
- [Devtooling Evaluation Notebook](https://app.hex.tech/00bffd76-9d33-4243-8e7e-9add359f25c7/app/d5da455e-b49a-47d6-a88d-dce1f679a02b/latest)
