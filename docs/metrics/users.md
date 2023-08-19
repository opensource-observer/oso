# Users

> This document outlines how we define and categorize blockchain users, and how we assign activity levels to them based on their onchain activity.

A **user** is a unique blockchain address that interacts with a smart contract and pays a gas fee back to the underlying network. 

Users may either be:
- Externally owned accounts (EOAs), ie, accounts managed by a private key
- Smart contract accounts (SCAs), ie, accounts controlled by a multisig or utilized account abstraction (ERC-4337)

## Types of Users

We also consider the timing and frequency of contracts interactions to determine the "value" of a user.

### High Value Users

A high value user is an account that has interacted with one or more of a project's smart contracts at least 10 times in the past 30 days.

### Low Value Users

A low value user is an account that has interacted with one or more of a project's smart contracts at least once (but less than 10 times) in the past 30 days.

### Inactive Users

An inactive user is an account that has not interacted with any of a project's smart contracts in the past 30 days.

### New Users

A new user is an account that had their first contract interaction with a project in the past 90 days.