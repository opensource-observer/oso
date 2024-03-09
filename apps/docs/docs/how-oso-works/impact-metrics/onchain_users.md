---
sidebar_position: 5
---

# Onchain Users

OSO maintains categories for users of a network, and assigns activity levels to them based on their activity patterns.

User metrics are typically queried by project (eg, `uniswap`), although they can also be queried by contract address (e.g., `0x123...`) and even across networks (e.g., `optimism` and `arbitrum`). For information about how transactions are logged, also see: [Onchain Activity](./onchain_activity).

## User Metrics

### total_users

The number of unique addresses interacting with the project's contracts.

### users_6_months

The number of unique users interacting with the project's contracts in the last 6 months.

### new_users

The number of users interacting with the project's contracts for the first time in the last 3 months.

## Active Users

### active_users

The number of users interacting with the project's contracts in the last 3 months.

### high_frequency_users

The number of active users who have made 1000+ transactions with the project's contracts in the last 3 months.

### more_active_users

The number of active users who have made 10-999 transactions with the project's contracts in the last 3 months.

### less_active_users

The number of active users who have made 1-9 transactions with the project's contracts in the last 3 months.

## Ecosystem Engagement

### multi_project_users

The number of users who have interacted with 3+ projects' contracts in the last 3 months.

## What About Account Abstraction?

On Ethereum, account abstraction is a feature that allows smart contracts to pay for gas fees on behalf of their users. As account abstraction becomes more prevalent, we will likely need to adjust our tracking to better account for this.

---

To contribute new metrics, please see our guide [here](../../contribute/impact-models)
