---
title: Update Your Project's Artifacts
sidebar_position: 4
---

:::important
You can update your project's artifacts by editing the project's `.yaml` file in [oss-directory](https://github.com/opensource-observer/oss-directory) and submitting a pull request. Always refer to the [project schema](https://github.com/opensource-observer/oss-directory/blob/main/src/resources/schema/project.json) for the latest fields. Edits that do not conform to the schema will be rejected.
:::

Version 7 of the oss-directory schema currently supports the following artifact sources:

## Code Repositories

- `github`: A GitHub organization or repository URL.

  Note: we have plans to support other code repositories in the future, such as GitLab and Bitbucket.

## Package Managers

- `npm`: An npm package URL, eg. `https://www.npmjs.com/package/@babel/core`.
- `crates`: A crates package URL, eg. `https://crates.io/crates/serde`.
- `pypi`: A pypi package URL, eg. `https://pypi.org/project/pandas/`.
- `go`: A go package URL (ideally hosted on GitHub), eg. `https://github.com/libp2p/go-libp2p`.

## Blockchain Addresses

- `blockchain`: An blockchain address.

  Note: We have specific requirements for metadata about these addresses, including `networks` and `tags` fields. To view the latest fields, see the [blockchain address schema](https://github.com/opensource-observer/oss-directory/blob/main/src/resources/schema/blockchain-address.json).

:::tip
The simplest way to add all contracts and factories associated with your project is to just include the deployer address in the project file with the `deployer` tag. We will then automatically index all contracts and factories that originate from the deployer address. If the deployer is on multiple EVM networks, you can use the `any_evm` network label instead of listing each network individually.
:::

## DefiLlama

- `defillama`: A list of DefiLlama protocol URLs, eg. `https://defillama.com/protocol/my-protocol-v1`.

## Open Collective

- `open_collective`: An Open Collective URL, eg. `https://opencollective.com/my-project`.

## Social Profiles

- `farcaster`: A Farcaster URL, eg. `https://warpcast.com/my-project`.
- `medium`: A Medium URL, eg. `https://medium.com/@my-project`.
- `mirror`: A Mirror URL, eg. `https://mirror.xyz/my-project`.
- `telegram`: A Telegram URL, eg. `https://t.me/my-project`.
- `twitter`: A Twitter (X) URL, eg. `https://x.com/my-project`.

## Websites

- `websites`: A list of associated website URLs, eg, `https://my-project.com`.

## Examples

We recommend the following examples of project files to help you get started:

- [opensource-observer](https://github.com/opensource-observer/oss-directory/blob/main/data/projects/o/opensource-observer.yaml)
- [libp2p](https://github.com/opensource-observer/oss-directory/blob/main/data/projects/l/libp2p.yaml)
- [pandas](https://github.com/opensource-observer/oss-directory/blob/main/data/projects/p/pandas.yaml)
- [safe-global](https://github.com/opensource-observer/oss-directory/blob/main/data/projects/s/safe-global.yaml)
- [uniswap](https://github.com/opensource-observer/oss-directory/blob/main/data/projects/u/uniswap.yaml)
- [wormhole](https://github.com/opensource-observer/oss-directory/blob/main/data/projects/w/wormhole.yaml)
