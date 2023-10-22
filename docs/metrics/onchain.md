# Onchain Metrics

> This document provides details on Open Source Observer's onchain metrics. Onchain metrics are typically queried by project (e.g., `uniswap`) and network (e.g., `optimism`), but they can also be queried by contract address (e.g., `0x123...`) and even across networks (e.g., `optimism` and `arbitrum`).

For information about onchain transactions, see here: [Onchain Transactions](./transactions.md)

## Indicators

### Contracts Deployed
Number of total smart contracts directly deployed by the project and its factories. Currently, this excludes deploying multisigs (e.g., Safes), ERC20, and ERC721 contracts.

### Total Transactions
Number of times a contract or group of contracts has been invoked over a specific time period.

### Total Fees
Sum of gas fees contributed to the network by a contract or group of contracts over a specific time period. Gas fees are denominated in the chain's gas token.

### Average Transaction Fee
The ratio of total fees to total transactions over a specific time period.

### Users
Count of unique addresses that have transacted with a contract or a group of contracts.

Users may either be:
- Externally owned accounts (EOAs), ie, accounts managed by a private key
- Smart contract accounts (SCAs), ie, accounts controlled by a multisig or utilized account abstraction (ERC-4337)

### Weekly Active Users
Count of users that have transacted at least once over a 7-day period.

### High Frequency Users
Count of users that have transacted 100 or more times over a 7-day period.

### High Frequency User Contribution
Count of total transactions from high frequency users over a 7-day period.

### Monthly Active Users
Count of users that have transacted at least once over a 30-day period.

### High Value Users
Count of monthly active users with 10 or more transactions.

### Low Value Users
Count of monthly active users with fewer than 10 transactions.

### High Value User Contribution
Count of total transactions from high value users over a 30-day period.

### 90-Day Active Users
Count of users that have transacted at least once over a 90-day period.

### New Users
Count of 90-day active users that had their first transaction in the last 90 days.

### Retained Users
Count of 90-day active users that had their first transaction more than 90 days ago.

### Inactive Users
Count of users that have not had any transactions in the last 90 days.

### User Churn Rate
The proportion of inactive users to the total number of users, excluding new users.

### Ecosystem Users
Count of users that are also active in at least two other projects in the same collection.

### Active Ecosystem Users
Count of active users that are also active in at least two other projects in the same collection.

## API Reference

The following event `typeId`s are relevant to gathering onchain metrics:

```
'CONTRACT_INVOKED': 10,
'USERS_INTERACTED': 11,
'CONTRACT_INVOKED_AGGREGATE_STATS': 12,
'CONTRACT_INVOCATION_DAILY_COUNT': 25,
'CONTRACT_INVOCATION_DAILY_FEES': 26
```