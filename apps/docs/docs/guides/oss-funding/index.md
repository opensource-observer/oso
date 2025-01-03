---
title: Upload Funding Data
sidebar_position: 7
---

:::info
We are coordinating with several efforts to collect, clean, and visualize OSS funding data, including [RegenData.xyz](https://regendata.xyz/), [Gitcoin Grants Data Portal](https://davidgasquez.github.io/gitcoin-grants-data-portal/), and [Crypto Data Bytes](https://dune.com/cryptodatabytes/crypto-grants-analysis). We maintain a [master CSV file](https://github.com/opensource-observer/oss-funding) that maps OSO project names to funding sources. It includes grants, direct donations, and other forms of financial support. We are looking for data from a variety of sources, including both crypto and non-crypto funding platforms.
:::

## Uploading Funding Data

---

Add or update funding data by making a pull request to [oss-funding](https://github.com/opensource-observer/oss-funding).

1. Fork [oss-funding](https://github.com/opensource-observer/oss-funding/fork).
2. Add static data in CSV (or JSON) format to `./uploads/`.
3. Ensure the data contains links to one or more project artifacts such as GitHub repos or wallet addresses. This is necessary in order for one of the repo maintainers to link funding events to OSS projects.
4. Submit a pull request from your fork back to [oss-funding](https://github.com/opensource-observer/oss-funding).

## Contributing Clean Data

---

Data collective members may also transform the data to meet our schema and add a CSV version to the `./clean/` directory. You can do this by following the same process shown above, except destined to the `./clean/` directory.

Submissions will be validated to ensure they conform to the schema and don't contain any funding events that are already in the registry.

Additions to the `./clean/` directory should include as many of the following columns as possible:

- `oso_slug`: The OSO project name (leave blank or null if the project doesn't exist yet).
- `project_name`: The name of the project (according to the funder's data).
- `project_id`: The unique identifier for the project (according to the funder's data).
- `project_url`: The URL of the project's grant application or profile.
- `project_address`: The address the project used to receive the grant.
- `funder_name`: The name of the funding source.
- `funder_round_name`: The name of the funding round or grants program.
- `funder_round_type`: The type of funding this round is (eg, retrospective, builder grant, etc).
- `funder_address`: The address of the funder.
- `funding_amount`: The amount of funding.
- `funding_currency`: The currency of the funding amount.
- `funding_network`: The network the funding was provided on (eg, Mainnet, Optimism, Arbitrum, fiat, etc).
- `funding_date`: The date of the funding event.

## Exploring Funding Data

---

You can read or copy the latest version of the funding data directly from the [oss-funding](https://github.com/opensource-observer/oss-funding) repo.

If you do something cool with the data (eg, a visualization or analysis), please share it with us!
