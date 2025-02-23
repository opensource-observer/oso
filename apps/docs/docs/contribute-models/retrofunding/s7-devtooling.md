---
title: "S7: Developer Tooling"
sidebar_position: 2
---

:::important
Retro Funding is shifting to an algorithm-driven evaluation process, ensuring funding decisions are transparent, scalable, and based on measurable impact. Instead of voting on projects directly, citizens will vote on impact-measuring algorithms. Each algorithm has a different strategy for allocating rewards. These models will evolve based on community feedback and proposals. You can view the source code and contribute your own models [here](https://github.com/ethereum-optimism/Retro-Funding).
:::

This document explains the initial evaluation methodology developed for the **Retro Funding S7: Developer Tooling Mission**, including:

- **Linking onchain projects to devtooling projects** based on package dependencies and developer engagement
- **Key metrics** used to seed the graph with "pretrust" assumptions
- **Three initial algorithms** for assigning weights to the graph and emphasizing the importance of different links

| Algorithm     | Goal                           | Best For                                                | Emphasis                                                                                           |
| ------------- | ------------------------------ | ------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **Arcturus**  | Reward widely adopted projects | Established, high-impact devtooling projects            | Adoption & ecosystem influence (prioritizes total dependents and downstream usage)                 |
| **Bellatrix** | Prioritize fast-growing tools  | New or rapidly expanding devtooling projects            | Growth & recent traction (favors projects with rising dependents, dev traction, and onchain usage) |
| **Canopus**   | Recognize developer engagement | Tools with high developer collaboration & contributions | Community & developer trust (weights GitHub engagement, contributions, and code quality)           |

## Context

In 2025, Optimism’s Retro Funding program is shifting to a "metrics-driven, humans-in-the-loop" approach. Instead of voting on projects, citizens vote on _algorithms_. Each algorithm represents a different strategy for rewarding projects. Algorithms will evolve in response to voting, community feedback, and new ideas over the course of the season.

This particular round—**Retro Funding S7: Developer Tooling**—focuses on open source compilers, libraries, debuggers, and other toolchains that help builders create cross-chain or interop-compatible apps on the Superchain. See the [round details on the Optimism governance forum](https://gov.optimism.io/t/retro-funding-dev-tooling-mission-details/9598) for more on the mission’s objectives.

### Expected Impact

The overall goals for this round include:

- Growing the number and variety of dev toolchains supporting cross-chain or interoperable features
- Expanding the Superchain developer community and network effects around open source tooling
- Demonstrating a tangible lift in cross-chain or onchain activity from robust tools

Because Retro Funding is _retroactive_, we place emphasis on demonstrable impact: the usage, adoption, and developer traction a project already has in the ecosystem.

### Scope

We can estimate the current size of Optimism's devtooling ecosystem by looking at the number of packages being imported by onchain builder projects:

- **344** projects with open source code and active deployments on the Superchain
- **8436** distinct packages in their aggregated dependency graphs
  - TypeScript (npm): 6663
  - Rust (crates): 1283
  - Python (pypi): 107
  - Other (Go, etc.): 383
- **981** packages can be traced to 98 devtooling projects previously applying for Retro Funding
- **1.8M** total devtooling links (excluding self-edges), of which **135K** connect onchain builders to past Retro Funded projects

We also track the number of developers contributing to those 344 onchain builder projects:

- **1.3K** developers made 1 or more commits in the past 6 months
- **942** unique developers made commits across at least 3 months (within that 6-month window), contributing to 206 distinct onchain projects

The dependency graph is large and rich!

## Evaluation Methodology

### Overview

The OSO pipeline code is contained in our `DevtoolingCalculator` class and related helpers. Below is a high-level flow:

1. **Data Collection**: Aggregate data from onchain projects (transactions, user counts), devtooling projects (GitHub metrics, package dependencies), and developers (commits, PRs, forks).
2. **Trust Graph**: Build a directed graph from Onchain Projects → Developers → Devtooling Projects.
3. **Initial Pretrust Assignment**: Seed the graph with pretrust scores in three ways:
   - Onchain projects get pretrust for their economic activity (e.g., transaction volume).
   - Devtooling projects get pretrust for GitHub signals (e.g., stars, forks, packages published).
   - Developers receive an initial reputation derived from the onchain projects they contribute to.
4. **EigenTrust Implementation**: Distribute trust iteratively using [OpenRank's EigenTrust model](https://docs.openrank.com/reputation-algorithms/eigentrust) until scores converge.
5. **Normalization & Ranking**: Filter out ineligible projects, then rank projects and allocate funding proportionally.

### Eligibility

A devtooling project must meet all of the following to be considered for a reward:

1. **Open Source**: It has a _public_ GitHub repository with a continuous history of public commits (including some activity in the last 6 months).
1. **Minimum Links**: The devtooling project must meet the following "centrality" thresholds within the Optimism ecosystem:
   - At least **three** qualified onchain builder projects have included this devtooling project in their dependency graph (see “What types of package links?” below), **or**
   - At least **ten** active onchain developers (i.e., devs who contributed to qualified onchain builder projects) have engaged with the devtooling project on GitHub (commits, issues, PRs, forks, stars, etc.).
1. **Qualified Onchain Projects**: The onchain builder projects referencing this devtooling project must themselves meet two conditions:
   - Verify GitHub and contract ownership on OP Atlas
   - Have at least 0.01 ETH in L2 gas fees (across the Superchain) in the past 6 months

<details>
<summary>What is meant by "public" in the Open Source requirement?</summary>

Public means that the repository is public on GitHub. In addition, activity will only be tracked by OSO if it was made at a time when the repository was public. Many projects start as private but become public over time. We do not track or backfill private activity. Similarly, we do not capture any developer activity made to private repositories.

</details>

<details>
<summary>How are package links established?</summary>

We use the [SBOMs](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/exporting-a-software-bill-of-materials-for-your-repository) of qualified onchain builder projects to track package links. In order to traced to a devtooling project, the package metadata must include a link to a public repository that is owned by the devtooling project.

</details>

<details>
<summary>Why do we use these particular thresholds?</summary>

We want to exclude inactive or unproven devtooling projects that happen to appear in random code repos but have no real usage. Likewise, we want to ensure the onchain builder projects generating trust are themselves active and verifiable on OP Atlas.

</details>

### Graph Construction

There are three types of core **nodes** in the graph:

- **Onchain Projects**, which hold economic pretrust and pass it on.
- **Developers**, who gain partial trust from the onchain projects they contribute to.
- **Devtooling Projects**, which receive trust both directly from onchain projects, via package dependencies, and indirectly from developers’ GitHub engagement.

Links between nodes, i.e., **edges**, are derived from the following relationships:

1. **Onchain Projects → Devtooling Projects** (Package Dependencies)

   For each package in the onchain project’s [Software Bill of Materials (SBOM)](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/exporting-a-software-bill-of-materials-for-your-repository), if that package is owned by a devtooling project, we add an edge from the onchain project to the devtooling project.

   We typically set the edge “event timestamp” for these dependencies to the time OSO last indexed them, so they are treated as “recent” unless older time-decay rules apply.

2. **Onchain Projects → Developers** (Commits)

   Whenever a developer commits code (or merges PRs) in an onchain project’s GitHub repository, we add an edge from the onchain project to that developer.

   At present, the code lumps all commits in a monthly bucket. We do _not_ differentiate between 1 commit or 100 commits in that month—just that the developer contributed.

   If a developer contributed to multiple onchain projects in the same month, each project → developer link is added.

3. **Developers → Devtooling Projects** (GitHub Engagement)

   Whenever a developer (from the set recognized above) engages with a devtooling project (commits, PRs, issues, forks, stars, or comments), we add an edge from that developer to the devtooling project.

   As with onchain commits, these events are grouped by month—1 PR or 10 PRs is treated as “the developer engaged in that month.”

<details>
<summary>Which types of packages are considered?</summary>

We primarly consider npm (JavaScript/TypeScript), crates (Rust), and pypi (Python) package links. We have some support for Go package links hosted on GitHub, although Go is generally not as relevant to the app-side of the onchain builder ecosystem.

We recognize that this is not a comprehensive list of all possible package links and dependencies.

In the future, we hope to include [git submodules](https://github.blog/open-source/git/working-with-submodules/) and GitHub Actions as a source of package links.

We are also open to adding more crypto-specific package managers (e.g., Soldeer) in the future.

</details>

<details>
<summary>How are multiple dependencies from the same onchain project to the same devtooling project handled?</summary>

We currently condense them into a single edge by package source (e.g., npm, crates, pypi). This is a design choice so that devtooling projects cannot trivially split code into multiple packages to artificially inflate edges.

</details>

<details>
<summary>What about historical dependencies?</summary>

We have plans to include historical dependency data in future iterations of the evaluation. Currently, however, our metrics are only on the latest dependency data.

</details>

<details>
<summary>What about self-loops (i.e., onchain projects that use their own devtooling packages)?</summary>

We do not currently allow self-loops. If an onchain project uses its own devtooling package, we exclude those edges from the graph. Similarly, a developer who commits to the same entity recognized both as an onchain project and devtooling project does not artificially double-dip.

</details>

<details>
<summary>What if a package is used by onchain projects that are not in OP Atlas?</summary>

For Retro Funding purposes, we do not currently track onchain projects that are not in OP Atlas. OSO has a larger registry of onchain projects, so we can simulate results if the project pool is expanded or different.

</details>

<details>
<summary>What about other ways of reusing code?</summary>

Other ways of reusing code, such as developing off a fork or a clone, or directly copying code, are not currently considered. In general, our assumption is that network effects will accrue around projects that are viewed as most legitimate by the community.

As this is only a first iteration of the devtooling evaluation, we are curious to see examples of projects that have their impact diluted by these alternative code reuse mechanisms.

</details>

<details>
<summary>What if two devtooling projects are closely related? Do they double count the same dev trust?</summary>

Yes, if a developer meaningfully engages with both devtooling projects, we treat those as separate edges. Overlaps can occur. But in subsequent versions, the community may propose ways to discount or unify certain highly coupled devtooling projects.

</details>

### Pretrust Metrics

Metrics about projects and developers are used as a way of seeding the EigenTrust algorithm with **pretrust** assumptions. All other things being equal, edges that involve nodes with higher pretrust values will be weighted more heavily in the EigenTrust algorithm.

Pretrust metrics are applied to each node in the graph:

1. **Onchain Projects**

   - Pretrust is derived from aggregated economic metrics like:
     - Transaction volume (count of Superchain transactions in the last 180 days)
     - Gas fees (cumulative L2 fees paid by users in the last 180 days)
     - Bot-filtered unique user count (unique addresses that interacted with the project’s contract)
   - Each metric is log-scaled and min-max normalized
   - The importance of each metric is multiplied by algorithm-specific weights.
   - We sum the weighted metrics for each onchain project, and then normalize again so the total across all onchain projects = 1.

2. **Devtooling Projects**

   - Pretrust is derived from the total number of published packages and GitHub metrics (stars, forks).
   - The importance of each metric is multiplied by algorithm-specific weights.
   - The same procedure of log-scaling, min-max normalization, weighting, and final normalization to ensure the total across devtooling projects = 1.

3. **Developer Reputation**

   - Pretrust is derived from the onchain project(s) a developer contributes to:
     1. Group the developer’s commit history by (`event_month`, `developer_id`).
     2. Identify which onchain projects they contributed to in that month.
     3. Sum the **onchain project pretrust** for those projects, then **divide** that sum by the number of onchain projects. This yields the “share” of trust the developer receives for that month.
     4. Accumulate these shares across all months.
   - Finally, we apply min-max normalization across all developers to produce `developer_reputation` between 0 and 1.

Not all nodes have significant pretrust, but those that do help “seed” the rest of the graph with trusted edges.

<details>
<summary>Why these metrics?</summary>

These metrics are relatively simple to measure and widely applicable to different types of projects.

</details>

<details>
<summary>Why are we dividing by the number of onchain projects contributed to in a month?</summary>

This ensures that if a developer works on multiple onchain projects _in the same time window_, they do not receive the full sum of each project’s pretrust. It is effectively splitting the combined trust among all relevant projects. We may refine this approach in future versions (e.g., weighting by lines changed, repository size, etc.).

</details>

<details>
<summary>Why log-scaling?</summary>

Onchain activity numbers (transactions, gas, user counts) span large orders of magnitude. Log-scaling avoids overshadowing smaller but still meaningful projects.

</details>

### Algorithm Settings & Weights

After constucting the graph and computing pretrust scores, we assign final weights to each edge before EigenTrust runs:

1. **Alpha**

   - The alpha parameter controls the portion of the EigenTrust output taken from the pretrust values vs. the iterative trust propagation step. See [below](#eigentrust) for more details of setting alpha values.
   - EigenTrust's default alpha is 0.5. This means 50% of trust remains with the original pretrust seeds each iteration, and 50% is re-distributed based on the adjacency matrix.
   - A higher alpha places more emphasis on raw pretrust; a lower alpha places more emphasis on iterative trust from usage/engagement.

1. **Time Decay**

   - By default, we reference the latest `event_month` in the dataset as `time_ref` and compute `(time_ref - event_month)` in years.
   - We apply an exponential decay factor, i.e., `exp(-decay_factor * change_in_years)`.
   - Algorithms can specificy separate decay factors for each type of edge in the YAML config.
     - e.g. `commit_to_onchain_repo` edges might have a smaller decay factor than `event_to_devtooling_repo`.

1. **Link-Type Weights**

   - Each of the two link types (i.e., package link, developer link) has a configurable base weight.
   - These weights have the effect of favoring one type of link over another.

1. **Event-Type Weights**
   - There are `event_type` weights for both GitHub events (e.g., commit code, forked, etc.) and package events (e.g., npm dependency added, crates dependency added, etc.).
   - These weights have the effect of favoring one type of event over another.
   - They can also be set to zero, effectively removing that link type from the graph.

All of these properties are configurable in each algorithm's associated YAML. We encourage the community to propose different settings that reflect how we want to reward certain forms of usage.

<details>
<summary>Can you apply different time decays to different types of events?</summary>

We implement this only for link types, not event types. More fine-grained control is entirely possible, but not currently implemented.

</details>

<details>
<summary>Can you penalize spammy engagement?</summary>

This is entirely possible, but not currently implemented.

</details>

### EigenTrust Propagation

We run the [EigenTrust](https://docs.openrank.com/openrank-sdk/sdk-references/eigentrust) algorithm to propagate trust through the weighted edges:

1. **Pretrust Vector**

   - We combine the onchain project pretrust, devtooling project pretrust, and developer reputation into one vector.
   - Example: If an onchain project i has a pretrust of 0.05, devtooling project j has a pretrust of 0.01, and developer d has 0.02, those are all entries in the same “seed” vector.

2. **Weighted Adjacency Matrix**

   - Each row i in the adjacency matrix (for node i) has outgoing edges to j with final weight `v_final`.
   - These are normalized in the EigenTrust process so that each row sums to 1, distributing i’s trust proportionally to its outbound edges.

3. **Iteration & Convergence**
   - EigenTrust typically converges in a handful of iterations on large graphs.
   - The final score for each node is the stable distribution of trust.

In the end, **devtooling projects** receive a final trust score that reflects:

- Their initial pretrust metrics
- How much trust flows from onchain projects that depend on them
- How much trust flows from reputable developers who engage with them

<details>
<summary>Why EigenTrust?</summary>

EigenTrust helps ensure funding goes to impactful devtooling projects by distributing trust through real-world dependencies and engagement. Instead of relying on raw GitHub metrics (which can be gamed), EigenTrust assigns higher scores to projects trusted by widely used onchain apps and respected developers. This prevents low-quality or spam projects from receiving disproportionate rewards.

For more details, see [this original paper](https://nlp.stanford.edu/pubs/eigentrust.pdf) and the [OpenRank EigenTrust docs](https://docs.openrank.com/openrank-sdk/sdk-references/eigentrust).

</details>

### Finalizing & Ranking

When EigenTrust converges, we focus on scores for **devtooling projects** only:

1. **Check Eligibility**

   - Any project that does **not** pass the thresholds for minimal usage (three onchain references, or ten active developer links) is marked ineligible and zeroed out.

2. **Aggregate Scores**

   - For each devtooling project, we take its EigenTrust score (v). If it’s ineligible, we set it to 0.
   - We then normalize so that the sum of devtooling scores = 1. This is the final fraction of the available S7 devtooling funds.

3. **Reward Distribution**
   - We can optionally apply a min/max reward cap. Then each project’s final trust fraction × (pool size) yields the reward.
   - The reward distribution parameters are determined by the Optimism Foundation and are not algorithm-specific.

<details>
<summary>How does OSO produce the “value flow” Sankey from onchain projects to devtooling projects?</summary>

After we have final devtooling scores, we use a method called **iterative proportional fitting (IPF)** to break down exactly how each devtooling project’s final trust is “sourced” from the onchain projects that connect to it.  
The pipeline exports a “detailed_value_flow_graph” CSV that can power visual diagrams of which onchain projects contributed to a devtooling project’s final score. This helps with attribution and transparency.

</details>

## Proposed Algorithms

Each algorithm references a different YAML file but shares the same underlying pipeline, with distinct weights and decays.

### Arcturus

This algorithm aims to reward projects with significant current adoption. It focuses on total dependents and downstream impact—how many developers and onchain users benefit from these tools. By recognizing well-established projects that already power much of the ecosystem, Arcturus seeks support cornerstone infrastructure that large numbers of builders rely on.

<details>
<summary>Weightings & Sample Results</summary>

Weightings for Arcturus:

- **Alpha**: High. The metrics used to establish pretrust have a relatively large impact on the final scores.
- **Time Decay**: Low. There is a small discount applied to older events, but not as much as other algorithms.
- **Link-Type Weights**: Package bias. The model prefers package dependencies over developer engagement.
- **Event-Type Weights**: Neutral. The model does not strongly favor one type of event over another.

Projects from Retro Funding 3 that score well in this algorithm include:

1. Ethers.js: https://github.com/ethers-io
2. OpenZeppelin: https://github.com/openzeppelin
3. Hardhat: https://github.com/nomicfoundation/hardhat
4. wevm: https://github.com/wevm
5. web3.js: https://github.com/web3/web3.js

</details>

### Bellatrix

This algorithm tries to identify projects that are rapidly growing in adoption and impact. It measures net gains in dependents, developer traction, and onchain usage over the past six months. By prioritizing growth metrics, it encourages new or recently revamped tools that quickly gain traction among onchain builders.

<details>
<summary>Weightings & Sample Results</summary>

Weightings for Bellatrix:

- **Alpha**: Low. The metrics used to establish pretrust have a relatively small impact on the final scores.
- **Time Decay**: High. There is a significant decay factor applied to older events.
- **Link-Type Weights**: Neutral. The model does not strongly favor one type of link over another.
- **Event-Type Weights**: Opinionated. The model prefers when projects add Rust over NPM packages, and applies different weights to different types of GitHub events.

Projects from Retro Funding 3 that score well in this algorithm include:

1. Foundry: https://github.com/foundry-rs
2. wevm: https://github.com/wevm
3. Alloy: https://github.com/alloy-rs
4. Pyth: https://github.com/pyth-network/pyth-sdk-rs
5. whatsabi: https://github.com/shazow/whatsabi

</details>

### Canopus

This algorithm measures a project’s developer engagement and utility across the onchain builder ecosystem. It looks not only at dependencies but also how many trusted developers (especially those known for smart contract work) commit, open pull requests, comment on issues, star, or fork these tools. This gives projects that improve the developer experience beyond offering npm / Rust packages a more even footing.

<details>
<summary>Weightings & Sample Results</summary>

Weightings for Canopus:

- **Alpha**: High. The metrics used to establish pretrust have a relatively large impact on the final scores.
- **Time Decay**: Low. There is a small decay factor applied to older events.
- **Link-Type Weights**: Developer bias. The model prefers developer engagement over package dependencies.
- **Event-Type Weights**: Neutral. The model does not strongly favor one type of event over another.

Projects from Retro Funding 3 that score well include:

1. Hardhat: https://github.com/nomicfoundation/hardhat
2. Prettier Solidity: https://github.com/prettier-solidity
3. OpenZeppelin: https://github.com/openzeppelin
4. Sourcify: https://github.com/ethereum/sourcify
5. blst: https://github.com/supranational/blst

</details>

## Contributing to the Model

We welcome improvements to:

1. **Data Coverage**
   - Integrate more package registries or additional GH events.
   - Include historical dependency data (time series) for more nuanced modeling.
2. **Pretrust Metrics**
   - Suggest more robust onchain metrics or different weighting for devtooling GitHub / package metrics.
3. **Algorithmic Weights**
   - Tweak link-type, event-type, or time-decay parameters in the YAML to reflect desired emphasis.
   - Or propose entirely new weighting logic.
4. **Scoring Method**
   - Compare EigenTrust with alternative ranking algorithms (PageRank, HITS, etc.).
   - See how each method aligns with the developer community’s sense of “impact.”

These are just a few of our ideas! All data and code can be found in the [Retro-Funding GitHub repo](https://github.com/ethereum-optimism/Retro-Funding).

## Further Resources

- [Retro Funding Algorithms Repo](https://github.com/ethereum-optimism/Retro-Funding)
- [Optimism Dev Tooling Mission Details](https://gov.optimism.io/t/retro-funding-dev-tooling-mission-details/9598)
- [Open Rank / EigenTrust Docs](https://docs.openrank.com/reputation-algorithms/eigentrust)
- [EigenTrust Original Paper](https://nlp.stanford.edu/pubs/eigentrust.pdf)
- [OSO Superchain S7 Metric Models](https://github.com/opensource-observer/oso/tree/main/warehouse/metrics_mesh/models/intermediate/superchain)
- [OSO’s Devtooling Evaluation Notebook](https://app.hex.tech/00bffd76-9d33-4243-8e7e-9add359f25c7/app/d5da455e-b49a-47d6-a88d-dce1f679a02b/latest)
