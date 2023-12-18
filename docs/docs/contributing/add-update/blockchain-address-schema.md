---
title: Blockchain Address Schema
sidebar_position: 3
---

# Blockchain Address Schema

The blockchain address schema is used in the [project schema](./project-schema) to validate blockchain addresses for projects.

The `address` field is the public blockchain address. On Ethereum and other networks compatible with the Ethereum Virtual Machine (EVM), public addresses all share the same format: they begin with 0x, and are followed by 40 alphanumeric characters (numerals and letters), adding up to 42 characters in total. Addresses are not case sensitive.

:::warning
If you are referencing a Safe multi-sig address, remember to remove the chain identifer from the beginning of the address (eg, remove the 'oeth:' prefix from the beginning of an Optimism Safe).
:::

The `networks` field is an array used to identify the blockchain network(s) that the address is associated with. Currently supported options are `mainnet`, `optimism`, and `arbitrum`.

## Tagging Addresses

The `tags` field is an array used to classify the address. Currently supported options are `eoa`, `safe`, `creator`, `deployer`, `factory`, `proxy`, `contract`, and `wallet`. In most cases, an address will have more than one tag.

- `eoa`, `contract`, `safe`: These tags are used to classify the address as an Externally Owned Account (EOA), a smart contract, or a Safe multi-sig wallet. We try to differentiate between smart contracts and Safe multi-sig wallets; with the former we seek to track event data and with the latter we seek to track funding data.
- `wallet`: This tag is used to classify the address as a wallet that should be monitored for funding events. This tag is only associated with addresses that are also tagged as `eoa` or `safe`.
- `creator`, `deployer`: These tags are interchangeable and used to classify an EOA address that is primarily used to for deploying smart contracts. We track these addresses to identify new smart contracts that are deployed by projects. We do not monitor them for funding events.
- `factory`: This tag is used to classify a smart contract address that is used to deploy other smart contracts. We capture event data from all contracts deployed by a factory contract.
- `proxy`: This tag is used to classify a proxy contract address. We currently do not handle proxy contracts differently from other smart contracts, therefore it is currently optional.

### Examples

#### EOA used for contract deployment

```
{
  "address": "0x1234567890123456789012345678901234567890",
  "tags": ["eoa", "deployer"],
  "networks": ["mainnet", "optimism"],
  "name": "My Deployer EOA"
}
```

#### EOA used for custodying funds

```
{
  "address": "0x1234567890123456789012345678901234567890",
  "tags": ["eoa", "wallet"],
  "networks": ["mainnet", "optimism", "arbitrum"],
  "name": "My Wallet EOA"
}
```

#### Safe used for custodying funds

```
{
  "address": "0x1234567890123456789012345678901234567890",
  "tags": ["safe", "wallet"],
  "networks": ["mainnet"],
  "name": "My Safe Wallet"
}
```

#### Factory smart contract

```
{
  "address": "0x1234567890123456789012345678901234567890",
  "tags": ["contract", "factory"],
  "networks": ["mainnet"],
  "name": "My Factory Contract"
}
```

# Full Schema

You can always access the most recent version of the schema [here](https://github.com/opensource-observer/oss-directory/blob/main/src/resources/schema/blockchain-address.json).

```
{
  "$id": "blockchain-address.json",
  "title": "Blockchain address",
  "type": "object",
  "description": "An address on a blockchain",
  "properties": {
    "address": {
      "type": "string"
    },
    "tags": {
      "type": "array",
      "minItems": 1,
      "items": {
        "enum": [
          "eoa",
          "safe",
          "creator",
          "deployer",
          "factory",
          "proxy",
          "contract",
          "wallet"
        ],
        "$comment": "Tags that classify the address. Options include: \n- 'eoa': Externally Owned Account \n- 'safe': Gnosis Safe or other multi-sig wallet \n- 'deployer' (or 'creator'): An address that should be monitored for contract deployment events \n- 'factory': A contract that deploys other contracts \n- 'proxy': Proxy contract \n- 'contract': A smart contract address \n- 'wallet': An address that should be monitored for funding events"
      }
    },
    "networks": {
      "type": "array",
      "minItems": 1,
      "items": {
        "enum": ["mainnet", "optimism", "arbitrum"]
      }
    },
    "name": {
      "type": "string"
    }
  },
  "required": ["address", "tags", "networks"]
}
```
