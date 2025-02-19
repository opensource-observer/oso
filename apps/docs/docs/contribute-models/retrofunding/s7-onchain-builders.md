---
title: "S7: Onchain Builders"
sidebar_position: 3
---

:::warning
This document is a work in progress, with placeholders in some of the important sections currently under development.
:::

This document explains how the **Retro Funding S7: Onchain Builders Mission** will evaluate project-level impact.

This model uses a direct scoring approach that aggregates onchain activity metrics (e.g., network activity, TVL, user activity) from multiple chains and normalizes them into a final per-project score.

Please note: This is a first iteration of our onchain builder evaluation. Your feedback and contributions are welcome!

## Context

In 2025, Optimism’s Retro Funding (RF) program continues to evolve toward a data-driven approach. This Onchain Builders mission focuses on projects that deploy code or operate smart contracts on the Superchain—particularly those that showcase meaningful ecosystem adoption through network activity, TVL, or user activity.

### Expected Impact

The goals for this Onchain Builders round are to:

- Reward projects that have successfully brought real economic or social activity onchain.
- Drive cross chain asset transfers and adoption of interop-compatible apps.
- Recognize projects with high momentum that lead to sticky TVL and network activity.

Our emphasis is on **actual onchain impact** rather than predictions of future growth.

### Scope

We can estimate the ecosystem size by looking at aggregated onchain metrics:

- **Projects**: The OSO dataset includes X unique onchain deployments recognized as "builder projects" on the Superchain.
- **Transaction Volume**: Over the past 6 months, these projects collectively handled Y transactions with Z total gas fees.
- **TVL**: The total value locked in these projects is estimated to be W (or X% of total Superchain TVL).
- **Monthly Active Addresses**: On average, these projects collectively engaged A distinct addresses (bot-filtered) per month.

## Evaluation Methodology

Our approach is powered by OSO’s 8-step aggregator pipeline (as shown in [`onchain_builders.py`](#the-code)):

1. **Instantiate** dataclasses with default parameters (e.g., data paths, weighting config).
2. **Load** the relevant YAML config—defining periods (past/current), chain weights, metric weights, etc.
3. **Load** raw CSV data—merging project-level info with a table of onchain metrics.
4. **Pre-Process** the data—pivoting by project and measurement period, grouping by chain, etc.
5. **Compute** variant scores (e.g., adoption, growth, retention) from current vs. past periods.
6. **Normalize** each metric variant across projects (e.g., min-max scaling).
7. **Weight & Aggregate** all the normalized metrics into a single score per project, using a power mean approach (or other aggregator).
8. **Output** final results and store them in CSV.

### Eligibility

A project must meet the following criteria to be considered for an onchain builder reward:

1. **Active Deployment**: The project has at least one verified contract deployment on the Superchain that paid ≥ 0.01 ETH in gas fees over the past 6 months.
2. **Bot-Filtered Usage**: The project has more than 25 addresses identified as non-bot participants.
3. **Timestamp**: The project’s earliest verified contract deployment must be at least 1 month old.

<details>
<summary>How do we classify non-bot addresses?</summary>
We apply a combination of known spam addresses, frequent self-transfers, and anomalous patterns to reduce the likelihood of awarding projects that rely on artificial usage. The approach is still evolving; if you see false negatives or false positives, please let us know.
</details>

### Metrics

The current YAML config (`onchain_builders_testing.yaml`) tracks the following raw metrics (by chain, for each project):

- **transaction_count_bot_filtered**: Total transactions minus known bot addresses.
- **transaction_gas_fee**: The total gas fees (in ETH or chain-native tokens) paid by these transactions.
- **monthly_active_farcaster_users**: A prototype measure capturing bridging of social usage signals (subject to change in future versions).
- **trace_count**: The count of internal contract calls or logs, used to approximate contract complexity or usage depth.

#### Variants

From these raw metrics, we derive three variant scores for each project:

1. **Adoption**: The current period’s metric value.
2. **Growth**: The difference between current and previous period, clipped at zero (i.e., negative growth is counted as zero).
3. **Retention**: The minimum of current and previous period’s metric, which helps reward sustained usage.

After computing these variants, the pipeline normalizes each column to a 0–1 range across all projects.

### Weighting & Aggregation

The pipeline allows multiple weighting layers:

- **Chain Weights**: We can apply different multipliers to each chain (e.g., weighting Base usage equally with Optimism usage).
- **Metric Weights**: We can define how heavily each raw metric should count (transaction_count, gas_fees, monthly_active_farcaster_users, etc.).
- **Variant Weights**: We can also decide how much to weight adoption vs. growth vs. retention.

Finally, we aggregate each project’s weighted normalized values into a single score:

- By default, we use a **power mean** aggregator with `p=2`, meaning the partial scores are squared, averaged, then square-rooted.
- Other aggregator choices (like sum, geometric mean, etc.) are supported.

### Finalizing Scores

After computing the final scores, projects are ranked in descending order. We then apply:

1. **Minimum Reward**: Ensures each qualified project receives at least a baseline amount.
2. **Maximum Reward Share**: Caps the share a single project can receive from the total budget.
3. **Normalization**: Re-scales final allocations to match the mission’s overall budget.

Projects that fail the eligibility checks are excluded from final rankings.

---

## Proposed Algorithms

Below is a simplified example of a single YAML config that might be used in this pipeline:

```yaml
data_snapshot:
  data_dir: "eval-algos/S7/data/onchain_testing"
  projects_file: "projects_v1.csv"
  metrics_file: "onchain_metrics_by_project.csv"

simulation:
  periods:
    "Dec 2024": "previous"
    "Jan 2025": "current"

  chains:
    BASE: 1.0
    OPTIMISM: 1.0

  metrics:
    transaction_count_bot_filtered: 0.30
    transaction_gas_fee: 0.30
    monthly_active_farcaster_users: 0.10
    trace_count: 0.30

  metric_variants:
    Adoption: 0.70
    Growth: 0.00
    Retention: 0.30

  aggregation:
    method: power_mean
    p: 2

allocation:
  budget: 1000000
  min_amount_per_project: 200
  max_share_per_project: 0.05
  max_iterations: 50
```

_(Note: These are sample results, not real data!)_

## Contributing

We welcome your help improving this methodology:

1. **Data Source Expansion**
   - Integrate additional onchain metrics or user labels to refine usage signals.
2. **Refined Weighting**
   - Suggest new weighting schemes, aggregator methods, or time decay parameters.
3. **Qualitative Feedback**
   - Compare final results to actual builder adoption or user sentiment and propose adjustments.

## Further Resources

- [Retro Funding Algorithms Repo](https://github.com/ethereum-optimism/Retro-Funding)
- [Optimism Builder Docs](https://docs.optimism.io/)
- [Open Source Observer aggregator references](https://docs.opensource.observer/docs/integrate/overview/)
- [onchain_builders.py Code](https://github.com/ethereum-optimism/Retro-Funding/blob/main/onchain_builders.py)
- [Data Normalization & Power Mean Explanation](https://en.wikipedia.org/wiki/Generalized_mean)
