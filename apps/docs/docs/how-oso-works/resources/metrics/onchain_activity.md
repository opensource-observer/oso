---
sidebar_position: 4
---

# Onchain Activity

Onchain metrics include projects' smart contracts, transaction volumes, and sequencer fee contribution.

Onchain metrics are typically queried by project (e.g., `uniswap`) and network (e.g., `optimism`), but they can also be queried by contract address (e.g., `0x123...`) and even across networks (e.g., `optimism` and `arbitrum`).

## Addesses Owned

For information about how addresses are tagged, please see: [Address Tagging](../../schema/artifact.md#tagging-addresses).

### num_contracts

The number of contracts directly associated with the project.

### num_deployers

The number of addresses that have deployed contracts for the project. _Coming soon!_

### num_wallets

The number of addresses that have custody of funds for the project. _Coming soon!_

## Transactions

Open Source Observer only tracks transactions that involve smart contracts, as most all smart contracts are open source and most widely-used smart contracts can be traced to projects with additional open source components.

Our primary focus is on transactions between externally owned account (EOA) addresses and smart contracts. We do not currently track the internal transactions between smart contracts, although their effects are captured in the aggregate transaction costs of the EOA to smart contract transactions. We also do not track transactions between EOAs, even though these are often facilitated by a frontend or wallet interface, because that information is not captured onchain.

For additional information about onchain user data, also see: [Onchain Users](./onchain_users).

### total_txns

The total number of onchain transactions with the project's contracts.

### txns_6_months

The total number of onchain transactions with the project's contracts in the last 6 months.

### first_txn_date

The date of the first onchain transaction with the project's contracts.

## Gas Usage

### total_l2_gas

The total Layer 2 gas used by the project's contracts.

### l2_gas_6_months

The total Layer 2 gas used by the project's contracts in the last 6 months.

---

To contribute new metrics, please see our guide [here](../../../contribute/impact-models)
