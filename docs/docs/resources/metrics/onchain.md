---
sidebar_position: 3
---

# Onchain Metrics

This document provides details on Open Source Observer's onchain metrics. Onchain metrics are typically queried by project (e.g., `uniswap`) and network (e.g., `optimism`), but they can also be queried by contract address (e.g., `0x123...`) and even across networks (e.g., `optimism` and `arbitrum`).

For information about onchain transactions, see here: [Onchain Transactions](./transactions)

## Addesses Owned

### `num_contracts`

The number of contracts directly associated with the project.

## Transactions

### `total_txns`

The total number of onchain transactions with the project's contracts.

### `txns_6_months`

The total number of onchain transactions with the project's contracts in the last 6 months.

### `first_txn_date`

The date of the first onchain transaction with the project's contracts.

## Gas Usage

### `total_l2_gas`

The total Layer 2 gas used by the project's contracts.

### `l2_gas_6_months`

The total Layer 2 gas used by the project's contracts in the last 6 months.

## Users

### `total_users`

The number of unique addresses interacting with the project's contracts.

### `users_6_months`

The number of unique users interacting with the project's contracts in the last 6 months.

### `new_users`

The number of users interacting with the project's contracts for the first time in the last 3 months.

### `active_users`

The number of users interacting with the project's contracts in the last 3 months.

### `high_frequency_users`

The number of active users who have made 1000+ transactions with the project's contracts in the last 3 months.

### `more_active_users`

The number of active users who have made 10-999 transactions with the project's contracts in the last 3 months.

### `less_active_users`

The number of active users who have made 1-9 transactions with the project's contracts in the last 3 months.

## Ecosystem Engagement

### `multi_project_users`

The number of users who have interacted with 3+ projects' contracts in the last 3 months.
