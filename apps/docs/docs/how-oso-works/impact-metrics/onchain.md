---
sidebar_position: 3
---

# Onchain

:::info
Onchain metrics include projects' smart contracts, transaction volumes, and sequencer fee contribution. Onchain metrics are typically queried by project (e.g., `uniswap`) and network (e.g., `optimism`), but they can also be queried by contract address (e.g., `0x123...`) and even across networks (e.g., `optimism` and `arbitrum`).
:::

## Addesses Owned

---

For information about how addresses are tagged, please see: [Address Tagging](../oss-directory/artifact.md#tagging-addresses).

### num_contracts

The number of contracts directly associated with the project.

### num_deployers

The number of addresses that have deployed contracts for the project. _Coming soon!_

### num_wallets

The number of addresses that have custody of funds for the project. _Coming soon!_

## Transactions

---

Open Source Observer only tracks transactions that involve smart contracts, as most all smart contracts are open source and most widely-used smart contracts can be traced to projects with additional open source components.

Our primary focus is on transactions between externally owned account (EOA) addresses and smart contracts. We do not currently track the internal transactions between smart contracts, although their effects are captured in the aggregate transaction costs of the EOA to smart contract transactions. We also do not track transactions between EOAs, even though these are often facilitated by a frontend or wallet interface, because that information is not captured onchain.

### total_txns

The total number of onchain transactions with the project's contracts.

### txns_6_months

The total number of onchain transactions with the project's contracts in the last 6 months.

### first_txn_date

The date of the first onchain transaction with the project's contracts.

## Gas Usage

---

### total_l2_gas

The total Layer 2 gas used by the project's contracts.

### l2_gas_6_months

The total Layer 2 gas used by the project's contracts in the last 6 months.

## Users

---

### total_users

The number of unique addresses interacting with the project's contracts.

### users_6_months

The number of unique users interacting with the project's contracts in the last 6 months.

### new_users

The number of users interacting with the project's contracts for the first time in the last 3 months.

## Active Users

---

### active_users

The number of users interacting with the project's contracts in the last 3 months.

### high_frequency_users

The number of active users who have made 1000+ transactions with the project's contracts in the last 3 months.

### more_active_users

The number of active users who have made 10-999 transactions with the project's contracts in the last 3 months.

### less_active_users

The number of active users who have made 1-9 transactions with the project's contracts in the last 3 months.

### multi_project_users

The number of users who have interacted with 3+ projects' contracts in the last 3 months.

---

To contribute new metrics, please see our guide [here](../../contribute/impact-models).
