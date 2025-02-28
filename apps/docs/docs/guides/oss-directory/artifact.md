---
title: Artifact
sidebar_position: 4
---

:::info
An **artifact** is a link or reference to work created by open source projects in the OSS Directory. An artifact can only belong to one project otherwise it will fail our validation checks.
:::

:::note
Our current schema only indexed data from three types of artifacts: GitHub organizations and repositories, NPM packages, and blockchain addresses. The `github`, `npm`, and `blockchain` fields in the [project schema](./project) are used to store arrays of artifacts associated with a particular project.
:::

## Artifact Identification

---

Each artifact is identified by either a `url` field representing a valid URL in the correct namespace or an `address` representing a public key address on a blockchain.

For example, a GitHub organization artifact would be identified by a `url` field that is a valid GitHub organization URL (eg, `https://github.com/opensource-observer`). A blockchain address artifact would be identified by an `address` field that is a valid blockchain address (eg, `0x1234567890123456789012345678901234567890`).

:::warning
An artifact may only exist once and may only be assigned to a single project. For example, if a GitHub organization is already associated with a project, it cannot be added to another project. Similarly, if a blockchain address is already associated with a project, it cannot be added to another project.
:::

## URL Schema

---

The URL schema is used to validate artifacts that contain public code contributions. Currently, the only supported URL-based artifacts are GitHub organizations and repositories and NPM packages.

Artifacts that use this schema are validated to ensure that the `url` field is a valid URL in the correct namespace. For GitHub artifacts, the URL must begin with `https://github.com/`. For NPM artifacts, the URL must begin with `https://www.npmjs.com/package/`. Remember, a URL can only be assigned to a single project. New artifacts will also be validated to ensure that they do not already exist in the directory.

You can view the schema for the URL field [here](https://github.com/opensource-observer/oss-directory/blob/main/src/resources/schema/url.json).

```json
{
  "$id": "url.json",
  "title": "URL",
  "type": "object",
  "description": "A generic URL",
  "properties": {
    "url": {
      "type": "string",
      "format": "uri"
    }
  },
  "required": ["url"]
}
```

## Blockchain Address Schema

---

The blockchain address schema is used to validate blockchain addresses for projects.

The `address` field is the public blockchain address. On Ethereum and other networks compatible with the Ethereum Virtual Machine (EVM), public addresses all share the same format: they begin with 0x, and are followed by 40 alphanumeric characters (numerals and letters), adding up to 42 characters in total. Addresses are not case sensitive. Addresses will be validated to ensure they meet both network-specific and general address requirements.

Remember, a blockchain address can only be assigned to a single project. New artifacts will also be validated to ensure that they do not already exist in the directory.

:::warning
If you are referencing a Safe multi-sig address, remember to remove the chain identifier from the beginning of the address (eg, remove the 'oeth:' prefix from the beginning of an Optimism Safe).
:::

### Supported EVM Networks

The `networks` field is an array used to identify the blockchain network(s) that the address is associated with. Currently supported options are:

- `mainnet`: The Ethereum mainnet.
- `arbitrum_one`: The Arbitrum L2 network.
- `optimism`: The Optimism L2 network.
- `base`: The Base L2 network.
- `metal`: The Metal L2 network.
- `mode`: The Mode L2 network.
- `frax`: The Frax L2 network.
- `zora`: The Zora L2 network.

We do not support testnets for any of these networks and do not intend to.

After an EVM blockchain address is validated and added to the directory, it will be stored as a unique address-network pair in the OSO database.

### Tagging Addresses

The `tags` field is an array used to classify the address. Currently supported options are `eoa`, `safe`, `deployer`, `factory`, `contract`, and `wallet`. In most cases, an address will have more than one tag.

The following tags are most frequently used to describe blockchain addresses:

- `deployer`: A deployer address.
- `eoa`: An externally owned account (EOA) address.
- `safe`: A multisig safe contract address.
- `wallet`: A wallet address. This tag is used to classify the address as a wallet that should be monitored for funding events. This tag is only associated with addresses that are also tagged as `eoa` or `safe`.

In previous versions of the schema, we enumerated contracts and factories with the following tags. These tags are still supported but no longer required since we index all contracts and factories associated with a project from its deployer(s).

- `contract`: A smart contract address.
- `factory`: A factory contract address.

### Examples

#### EOA used for contract deployment

```json
{
  "address": "0x1234567890123456789012345678901234567890",
  "tags": ["eoa", "deployer"],
  "networks": ["mainnet", "optimism"],
  "name": "My Deployer EOA"
}
```

#### EOA used for custodying funds

```json
{
  "address": "0x1234567890123456789012345678901234567890",
  "tags": ["eoa", "wallet"],
  "networks": ["mainnet", "optimism", "arbitrum"],
  "name": "My Wallet EOA"
}
```

#### Safe used for custodying funds

```json
{
  "address": "0x1234567890123456789012345678901234567890",
  "tags": ["safe", "wallet"],
  "networks": ["mainnet"],
  "name": "My Safe Wallet"
}
```

### Full Schema

You can always access the most recent version of the schema [here](https://github.com/opensource-observer/oss-directory/blob/main/src/resources/schema/blockchain-address.json).

The full schema for the blockchain address field is as follows. Note that it includes `networks` that are not currently indexed but are planned for future versions.

```json
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
          "contract",
          "creator",
          "deployer",
          "eoa",
          "factory",
          "proxy",
          "safe",
          "wallet"
        ],
        "$comment": "Tags that classify the address. Options include: \n- 'eoa': Externally Owned Account \n- 'safe': Gnosis Safe or other multi-sig wallet \n- 'deployer' (or 'creator'): An address that should be monitored for contract deployment events \n- 'factory': A contract that deploys other contracts \n- 'proxy': Proxy contract \n- 'contract': A smart contract address \n- 'wallet': An address that should be monitored for funding events"
      }
    },
    "networks": {
      "type": "array",
      "minItems": 1,
      "items": {
        "enum": [
          "any_evm",
          "arbitrum_one",
          "base",
          "frax",
          "mainnet",
          "matic",
          "metal",
          "mode",
          "optimism",
          "pgn",
          "zora",
          "linea",
          "zksync_era",
          "polygon_zkevm",
          "scroll",
          "mantle"
        ]
      }
    },
    "name": {
      "type": "string"
    }
  },
  "required": ["address", "tags", "networks"]
}
```

## Contributing

---

Artifacts are updated and added to the OSS Directory by members of the Data Collective. To learn more about contributing to the OSS Directory, start [here](../../projects). If you are interested in joining the Data Collective, you can apply [here](https://www.kariba.network/).
