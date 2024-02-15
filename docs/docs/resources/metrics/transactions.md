# Onchain Transactions

> This document explains the concept of onchain transactions. It highlights different types of transactions and the ones that are tracked by Open Source Observer.

For information about onchain metrics, see here: [Onchain Metrics](./onchain)

A **transaction** involves transferring onchain assets from one blockchain address to another, often via smart contracts. When a transaction is proposed, the user must also specify a **gas price**, which determines the transaction's priority and processing time. The higher the gas price, the faster the transaction is processed.

## Types of Transactions

### Between EOA and EOA

An EOA is an externally owned account.

EOA to EOA transactions are usually payment or transfer transactions between people or between accounts controlled by the same person. These transactions don't involve any smart contracts.

Example: transferring ETH on Ethereum.

### Between EOA and Smart Contract

These transactions are usually initiated by the EOA by calling a smart contract function. The EOA pays a gas fee to the network to execute the transaction.

We are able to track these transactions because they are signed onchain by the EOA.

Example: minting an NFT on Polygon.

### Between Smart Contract and Smart Contract

These transactions are also referred to as _internal transactions_.

A smart contract calls a function on another smart contract, and this event triggers the execution of additional logic. This is often the behind-the-scenes work that happens after a user initiates an EOA to smart contract interaction.

Example: the contracts that facilitate a token swap on a decentralized exchange.

## Transactions Tracked by Open Source Observer

Open Source Observer only tracks transactions that involve smart contracts, as most all smart contracts are open source and most widely-used smart contracts can be traced to projects with additional open source components.

Our primary focus is on transactions between EOAs and smart contracts. We do not currently track the internal transactions between smart contracts, although their effects are captured in the aggregate transaction costs of the EOA to smart contract transactions.

We do not track transactions between EOAs, even though these are often facilitated by a frontend or wallet interface, because that information is not captured onchain.

### What About Account Abstraction?

On Ethereum, account abstraction is a feature that allows smart contracts to pay for gas fees on behalf of their users. As account abstraction becomes more prevalent, we will likely need to adjust our tracking to better account for this.
