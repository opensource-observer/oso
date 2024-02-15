---
title: Core Concepts
sidebar_position: 1
---

OSO datasets are built from four primary building blocks:

- Collections
- Projects
- Artifacts
- Events

A collection is a group of projects. A project is a group of artifacts. An event is an interaction with an artifact. These building blocks are used to create a data model that can be used to understand the impact of open source projects.

It is easy to define new collections, projects, and artifacts in our [OSS
Directory](https://github.com/opensource-oberver/oss-directory). Once these
exist, we will automatically start collecting event data for them.

## Collections

Collections are used to group projects together. For example, a collection may include all projects that are part of a particular ecosystem or all projects that are dependent on a given developer library.

A collection is validated by confirming that all of its projects are valid.

To learn more, check out the [collection schema](../resources/schema/collection) in our resources section.

## Projects

Projects are used to group artifacts together. For example, a project may include a GitHub organization, a blockchain address used for holding funds, and a NPM package.

In order to instantiate a project, we require a unique slug and a GitHub URL that is not owned by any other project. Project metadata, including its name and tagline, can also be be captured. Once instantiated, a project entry can be updated to include additional artifacts.

Critically, artifacts can only belong to one project. We run validation checks to ensure that artifacts are not duplicated across projects.

To learn more, check out the [project schema](../resources/schema/project) in our resources section.

## Artifacts

Artifacts are used to store information about work artifacts created by open source projects in the OSS Directory. For example, a GitHub organization artifact would be identified by a `url` field that is a valid GitHub organization URL (eg,`https://github.com/opensource-observer`) and a blockchain address artifact would be identified by an `address` field that is a valid blockchain address (eg, `0x1234567890123456789012345678901234567890`).

Some artifacts include additonal tags that are used as instructions for OSO's indexers. For example, a blockchain address with a `wallet` tag will be monitored for financial transactions and changes in token balances. A blockchain address with a `deployer` tag will be monitored for smart contract deployments. Any contracts deployed by a deployer will be associated with the deployer's project. Similarly, any contracts deployed by factories deployed by a deployer will also be associated with the deployer's project.

Tags are also used to indicate the network the address is used on. For example, a deployer may be active on both the Ethereum mainnet and the Optimism network.

OSO creates additional artifacts when a user interacts with a project. For example, when a user interacts with a project's GitHub repository, OSO creates a GitHub user artifact for that user. When a user interacts with a project's blockchain address, OSO creates a blockchain address artifact for that user.

To learn more, check out the [artifact schema](../resources/schema/artifact) in our resources section.

## Events

Events are used to store information about transactions or other activities involving a project's artifacts. These could include a code commit, a package download, or a smart contract interaction.

Every event is associated with an artifact that belongs to a single project. For example, a GitHub commit event is an event `from` a GitHub user artifact `to` a GitHub repo artifact owned by a single project. Similarly, a blockchain transaction event would be an event `from` a blockchain address artifact `to` another blockchain address artifact owned by a single project.

The `to` and `from` relationships between artifacts in an event are critical to OSO's ability to understand the impact of a project's activities and situate it in the context of overall network / ecosystem activity.

To learn more, check out the [event schema](../resources/schema/event) in our resources section.

## Example

Here's an example of how these building blocks can be used to model a collection of projects:

```yaml
- Collection: IPFS                            # projects in the IPFS ecosystem
  - Project: IPFS                             # IPFS GitHub organization
    - Artifact: https://github.com/ipfs/ipfs  # IPFS monorepo
    - Artifact: https://github.com/ipfs/kubo  # Kubo
    - Artifact: https://github.com/ipfs/boxo  # Boxo
    - Artifact: https://github.com/ipfs/helia # helia
  - Project: IPLD                             # IPLD GitHub organization
    - Artifact: https://github.com/ipld/ipld  # IPLD monorepo
    - Artifact: https://github.com/ipld/go-ipld-prime # go-ipld-prime
```
