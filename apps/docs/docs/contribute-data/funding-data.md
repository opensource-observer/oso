---
title: Upload Funding Data
sidebar_position: 8
---

:::info
We are coordinating with several efforts to collect, clean, and visualize OSS funding data, including [RegenData.xyz](https://regendata.xyz/), [Gitcoin Grants Data Portal](https://davidgasquez.github.io/gitcoin-grants-data-portal/), and [Crypto Data Bytes](https://dune.com/cryptodatabytes/crypto-grants-analysis). We maintain a [master CSV file](https://github.com/opensource-observer/oss-funding) that maps OSO project names to funding sources. It includes grants, direct donations, and other forms of financial support. We are looking for data from a variety of sources, including both crypto and non-crypto funding platforms.
:::

Add or update funding data by making a pull request to [oss-funding](https://github.com/opensource-observer/oss-funding).

1. Fork [oss-funding](https://github.com/opensource-observer/oss-funding/fork).
2. Add static data in CSV (or JSON) format to `./uploads/`.
3. Ensure the data contains links to one or more project artifacts such as GitHub repos or wallet addresses. This is necessary in order for one of the repo maintainers to link funding events to OSS projects.
4. Submit a pull request from your fork back to [oss-funding](https://github.com/opensource-observer/oss-funding).
