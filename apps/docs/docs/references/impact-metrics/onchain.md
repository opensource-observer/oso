---
sidebar_position: 3
---

# Onchain

:::info
Onchain metrics include projects' smart contracts, transaction volumes, and sequencer fee contribution. Onchain metrics are typically queried by project (e.g., `uniswap`) and network (e.g., `OPTIMISM`), but they can also be queried by contract address (e.g., `0x123...`) and even across networks (e.g., `OPTIMISM` and `BASE`).
:::

## Current Metrics

---

The latest version of our code metrics model can be viewed [here](https://models.opensource.observer/#!/model/model.opensource_observer.onchain_metrics_by_project_v1#description). For information about how addresses are tagged, please see: [Address Tagging](../../guides/oss-directory/artifact.md#tagging-addresses).

### days_since_first_transaction

**Days Since First Transaction**: Number of days since the project's first transaction.

### active_contract_count_90_days

**Active Contract Count (90 Days)**: Number of active contracts in the last 90 days.

### transaction_count

**Transaction Count**: Total number of transactions.

### transaction_count_6_months

**Transaction Count (6 Months)**: Total transactions in the last 6 months.

### gas_fees_sum

**Gas Fees Sum**: Total gas fees incurred by the project.

### gas_fees_sum_6_months

**Gas Fees Sum (6 Months)**: Total gas fees incurred in the last 6 months.

### address_count

**Address Count**: Total number of unique addresses interacting with the project.

### address_count_90_days

**Address Count (90 Days)**: Number of unique addresses interacting in the last 90 days.

### new_address_count_90_days

**New Address Count (90 Days)**: Number of new addresses in the last 90 days.

### returning_address_count_90_days

**Returning Address Count (90 Days)**: Number of returning addresses in the last 90 days.

### high_activity_address_count_90_days

**High Activity Address Count (90 Days)**: Number of high activity addresses in the last 90 days.

### medium_activity_address_count_90_days

**Medium Activity Address Count (90 Days)**: Number of medium activity addresses in the last 90 days.

### low_activity_address_count_90_days

**Low Activity Address Count (90 Days)**: Number of low activity addresses in the last 90 days.

### multi_project_address_count_90_days

**Multi-Project Address Count (90 Days)**: Number of addresses interacting with multiple projects in the last 90 days.

---

To contribute new metrics, please see our guide [here](../../contribute-models/data-models).
