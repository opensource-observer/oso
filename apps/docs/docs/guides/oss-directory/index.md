---
title: OSS Directory
sidebar_position: 1
---

:::info

The [OSS Directory](https://github.com/opensource-observer/oss-directory) serves as the "source of truth" for the projects and collections that are discoverable on Open Source Observer. While the directory may never be complete, it is actively maintained. We welcome community contributions of new projects and collections, as well as updates to existing entries. This directory is a public good, free to use and distribute.
:::

## Directory Structure

The OSS Directory is organized into two main folders:

- `./data/projects` - each file represents a single open source project and contains all of the artifacts for that project.
  - See `./src/resources/schema/project.json` for the expected JSON schema
  - Files should be named by the project `name`
  - A project's `name` must be globally unique. If there is a conflict in chosen `name`, we will give priority to the project that has the associated GitHub organization
  - In most cases, we adopt the GitHub organization name as the `name`. If the project is not associated with a GitHub organization, you try to use the project name followed by the repo owner as the `name`.
- `./data/collections` - each file represents a collection of projects that have some collective meaning (e.g. all projects in an ecosystem).
  - See `./src/resources/schema/collection.json` for the expected JSON schema
  - Collections are identified by their unique `name`

## Collections

---

Collections are used to group projects together. For example, a collection may include all projects that are part of a particular ecosystem or all projects that are dependent on a given developer library.

```yaml
name: my-collection
display_name: My Collection
projects:
  - project-name1
  - project-name2
  - project-name3
```

A collection is validated by confirming that all of its projects are valid. Please consult the [collection schema](./collection) for more information.

## Projects

---

Projects are used to group artifacts together. For example, a project may include a GitHub organization, an NPM package, and a blockchain address used for holding funds.

```yaml
name: opensource-observer
display_name: Open Source Observer
github:
  - url: https://github.com/opensource-observer
npm:
  - url: https://www.npmjs.com/package/oss-directory
blockchain:
  - address: "0x87feed6162cb7dfe6b62f64366742349bf4d1b05"
    networks:
      - mainnet
      - optimism
    tags:
      - eoa
      - wallet
```

In order to instantiate a project, we require a unique `name` and a GitHub URL that is not owned by any other project. Project metadata, including its `display_name` and `description`, can also be captured. Once instantiated, a project entry can be updated to include additional artifacts.

Critically, artifacts can only belong to one project. We run validation checks to ensure that artifacts are not duplicated across projects. Please consult the [project schema](./project) for more information.

## Artifacts

---

Artifacts are used to store information about work artifacts created by open source projects in the OSS Directory.

For example, here is the GitHub organization artifact (identified by a `url` field) that belongs to Open Source Observer's project file.

```yaml
github:
  - url: https://github.com/opensource-observer
```

Here is the NPM package artifact (identified by a `url` field) that belongs to Open Source Observer's project file.

```yaml
npm:
  - url: https://www.npmjs.com/package/oss-directory
```

Blockchain address artifacts include additional tags that are used as instructions for OSO's indexers. For example, a blockchain address with a `wallet` tag will be monitored for financial transactions and changes in token balances. A blockchain address with a `deployer` tag will be monitored for smart contract deployments. Any contracts deployed by a deployer will be associated with the deployer's project. Similarly, any contracts deployed by factories deployed by a deployer will also be associated with the deployer's project.

Tags are also used to indicate the network the address is used on. For example, a deployer may be active on both the Ethereum mainnet and the Optimism network.

Here is a blockchain address artifact that belongs to Open Source Observer's project file.

```yaml
blockchain:
  - address: "0x87feed6162cb7dfe6b62f64366742349bf4d1b05"
    networks:
      - mainnet
      - optimism
    tags:
      - eoa
      - wallet
```

To learn more, check out the [artifact schema](./artifact).

## Example

---

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

Once these entries are submitted to the OSS Directory, OSO will add them to the next data indexing job. After indexing is complete, metrics about these artifacts, projects, and collections will be available through the OSO API.
