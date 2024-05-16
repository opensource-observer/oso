---
title: Update Project Data
sidebar_position: 2
---

:::info
Add or update data about a project by making a pull request to the OSS Directory.
When a new project is added to OSS directory, we automatically index relevant
data about its history and ongoing activity so it can be queried via our API, included
in metrics dashboards, and analyzed by data scientists.
:::

## Quick Steps

---

Add or update project data by making a pull request to [OSS Directory](https://github.com/opensource-observer/oss-directory).

1. Fork [OSS Directory](https://github.com/opensource-observer/oss-directory/fork).
2. Locate or create a new project `.yaml` file under `./data/projects/`.
3. Link artifacts (ie, GitHubs, npm packages, blockchain addresses) in the project `.yaml` file.
4. Submit a pull request from your fork back to [OSS Directory](https://github.com/opensource-observer/oss-directory).
5. Once your pull request is approved, your project will automatically be added to our daily indexers. It may take longer for some historical data (eg, GitHub events) to show up as we run backfill jobs less frequently.

## Schema Overview

---

The latest schema version is Version 5. In this schema, we replace the field `slug` with `name` and the previous `name` field with `display_name`.

:::important
The `name` field is the unique identifier for the project and **must** match the name of the project file. For example, if the project file is `./data/projects/m/my-project.yaml`, then the `name` field should be `my-project`. As a convention, we usually take the GitHub organization name as the project `name`. If the project is a standalone repo within a larger GitHub organization or personal account, you can use the project name followed by the repo owner as the name, separated by hyphens.
:::

### Fields

The schema currently contains the following fields:

- `version`: The version of the schema you are using. The latest version is Version 5. This is a required field.
- `name`: The unique identifier for the project. This is usually the GitHub organization name or the project name followed by the repo owner, separated by hyphens. This is a required field.
- `display_name`: The name of the project. This is a required field.
- `description`: A brief description of the project.
- `github`: The GitHub URL of the project. This is a list of URLs, as a project can have multiple GitHub URLs. In most cases, the first and only URL will be the main GitHub organization URL. You don't need to include all the repositories that belong to the organization, as we will automatically index all of them.
- `npm`: The npm URL of a package owned the project. This is a list of URLs, as a project can have multiple npm URLs.
- `blockchain`: A list of blockchain addresses associated with the project. Each address should include the address itself, the networks it is associated with, and any tags that describe the address. The most important addresses to include are deployers and wallets. We use deployers to trace all contracts deployed by a project, and wallets to trace all transactions made by a project.

### Supported Blockchain Networks and Tags

The OSS Directory currently supports the following blockchain networks, which can be enumerated in the `networks` field of a blockchain address:

- `mainnet`: The Ethereum mainnet.
- `arbitrum-one`: The Arbitrum L2 network.
- `optimism`: The Optimism L2 network.
- `base`: The Base L2 network.
- `metal`: The Metal L2 network.
- `mode`: The Mode L2 network.
- `frax`: The Frax L2 network.
- `zora`: The Zora L2 network.

We do not support testnets for any of these networks and do not intend to.

The following tags can be used to describe blockchain addresses:

- `deployer`: A deployer address.
- `eoa`: An externally owned account (EOA) address.
- `safe`: A multisig safe contract address.
- `wallet`: A wallet address. This tag is used to classify the address as a wallet that should be monitored for funding events. This tag is only associated with addresses that are also tagged as `eoa` or `safe`.

In previous versions of the schema, we enumerated contracts and factories with the following tags. These tags are still supported but no longer required since we index all contracts and factories associated with a project from its deployer(s).

- `contract`: A smart contract address.
- `factory`: A factory contract address.

Read below for more detailed steps on how to add or update project data or consult the [schema](../how-oso-works/oss-directory/) for more information.

## Detailed Steps

---

Here's a more detailed set of instructions for first-time contributors.

### 1. Fork OSS Directory

- Navigate to the [OSS Directory](https://github.com/opensource-observer/oss-directory) repo.

- Click the "Fork" button in the upper right corner of this page. This will create a copy of the repository in your GitHub account. It's best practice to keep the same repository name, but you can change it if you want.

:::tip
If you run into issues, check out [GitHub's instructions](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo) for forking an open source software repository.
:::

### 2. Locate or create a new project file

- Every project file is a `.yaml` file under `./data/projects/` that looks like this:

  ```yaml
  version:
  name:
  display_name:
  github:
    - url:
  ```

- The directory is organized by the first letter of the project name. For example, if the project name is `my-project`, you can find it under `./data/projects/m/my-project.yaml`.
- Our project names and filenames are derived from a project's GitHub organization or repository name. Therefore, the easiest way to see if a project already exists in our directory is to search for its GitHub organization name. For example, if you wanted to see if we are indexing repos that belong to https://github.com/opensource-observer, then you would search for `opensource-observer` and you would discover a project page at `./data/projects/o/opensource-observer.yaml`.
- If the project doesn't exist, you can create a new `.yaml` file under `./data/projects/` In most cases, you should simply use the GitHub organization name (eg, `my-new-org`) as the name and filename (eg, `./data/projectsm/my-new-org.yaml`).
- If the project is not associated with a GitHub organization, you can use the project name followed by the repo owner as the name, separated by hyphens (eg, `my-repo-my-org`), and the same convention for the filename (eg, `./data/projects/m/my-repo-my-org.yaml`).
- Initialize the new project with the following fields:
  - `version`: The version of the schema you are using. The latest version is Version 3. You can learn more about the schema [here](../how-oso-works/oss-directory/schema-updates).
  - `name`: The unique identifier for the project. This is usually the GitHub organization name or the project name followed by the repo owner, separated by hyphens.
  - `display_name`: The name of the project.
  - `github`: The GitHub URL of the project. This is a list of URLs, as a project can have multiple GitHub URLs. In most cases, the first and only URL will be the main GitHub organization URL. You don't need to include all the repositories that belong to the organization, as we will automatically index all of them.

### 3. Link artifacts to the project

- Add artifacts to the project file. Artifacts are the different types of data that we index for a project. You can find the list of artifacts in the [schema](../how-oso-works/oss-directory/artifact). Here's an example of a project file with artifacts:

  ```yaml
  version:
  name:
  display_name:
  github:
    - url:
    - url:
  npm:
    - url:
    - url:
  blockchain:
    - address:
      tags:
        -
      networks:
        -
  ```

- Here's an example of a project `.yaml` file:

  ```yaml
  version: 5
  name: opensource-observer
  display_name: Open Source Observer
  github:
  - url: https://github.com/opensource-observer
  npm:
  - url: https://www.npmjs.com/package/oss-directory
  blockchain:
  - address: "0x87fEEd6162CB7dFe6B62F64366742349bF4D1B05"
      tags:
      - eoa
      networks:
      - optimism
      - mainnet
  - address: "0xc5bfce27e0e7a7d7731bc23b92ebc62b9ed63b83"
      networks:
      - optimism
      tags:
      - safe
      - wallet
  - address: "0x5cBd6362e6F222D2A0Feb89f32566ebd27091B98"
      networks:
      - arbitrum-one
      tags:
      - safe
      - wallet
  ```

:::info
Some projects may own a lot of blockchain addresses. The most important addresses to include in your PR are deployers and wallets. We use deployers to trace all contracts deployed by a project, and wallets to trace all transactions made by a project. If you are unsure about which addresses to include, you can ask in the PR thread.
:::

### 4. Submit a pull request from your fork to our repository

- Save your changes and open a pull request from your fork to the [OSS Directory](https://github.com/opensource-observer/oss-directory).
- If you are adding multiple new projects, you can include them all in the same pull request, but please provide some comments to help us understand your changes.
- Your submission will be reviewed by a maintainer before approving the pull request. If there are any issues, you will be notified in the pull request thread.
- Your submission will be merged once it is approved by a maintainer. Merging the pull request will trigger automated validation of the artifacts you added. If there are any issues or duplicates found, the pull request will be rejected and you will be notified in the pull request thread.
- Once the pull request is merged successfully, your project will be added to the indexing queue for inclusion in all subsequent data updates.

:::tip
If you run into issues, check out [GitHub's instructions](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork) for creating a pull request from a fork.
:::

### 5. Monitor indexing status of your project data

Once your pull request is merged, you can check whether your project data has been indexed by querying [our API](https://cloud.hasura.io/public/graphiql?endpoint=https://opensource-observer.hasura.app/v1/graphql).

Note that our indexer currently runs every 24 hours at 02:00 UTC. Therefore, it may take up to 24 hours for your project data to be fully indexed. Backfills are run periodically to ensure that all data is indexed. If you don't see any historic event data for your project, than the most likely reason is that the backfill has not yet been run.

## Bulk Updates

---

To make bulk updates, we recommend cloning the [OSS Directory](https://github.com/opensource-observer/oss-directory) repo and making changes locally. Then, submit a complete set of project updates via one pull request.

Given that the project data may come in all sorts of formats, we have not included a script that will work for all cases. We have included a [few scripts](https://github.com/opensource-observer/oss-directory/tree/main/src/scripts) as examples. These take CSV, TOML, or JSON files that contain a list of projects and associated artifacts.

If you need help making a bulk update, please [open an issue](https://github.com/opensource-observer/oss-directory/issues) and tag one of the maintainers.
