---
title: Upload Funding Data
sidebar_position: 7
---

:::info
We are working closely with [DAOstar](https://daostar.org/) to collect, clean, and visualize OSS funding data in accordance with the [DAOIP-5](https://github.com/metagov/daostar/blob/main/DAOIPs/daoip-5.md) standard. We maintain a [repository](https://github.com/opensource-observer/oss-funding) that maps OSO project names to funding sources. It includes grants, direct donations, and other forms of financial support. We are looking for data from a variety of sources, including both crypto and non-crypto funding platforms.
:::

## Uploading Funding Data

Add or update funding data by making a pull request to [oss-funding](https://github.com/opensource-observer/oss-funding).

1. Fork [oss-funding](https://github.com/opensource-observer/oss-funding/fork).
2. Add static data in CSV.
3. Use our libraries pyoso and/or oss-directory to identify projects that are already in OSO.
4. Submit a pull request from your fork back to [oss-funding](https://github.com/opensource-observer/oss-funding).

## Schema

Here is the current schema for indexing funding data:

- `to_project_name`: The name of the project as specified in OSS Directory. See [here](https://github.com/opensource-observer/oss-directory) for more info. Leave blank if the project is not yet in OSS Directory.
- `amount`: The amount of funding in USD equivalent at the time of the funding event.
- `funding_date`: The approximate date when the project received funding. Date format is `YYYY-MM-DD` (ie, '2024-01-17').
- `from_funder_name`: The name of the funder as specified in the funder's YAML file. See more details below.
- `grant_pool_name`: The name of the funding round or grants program.
- `metadata`: Optional metadata from the grants program in JSON format.

## Funder Profiles

Funders in oss-funding are registered as YAML files. Each funder should have its own directory in `./data/funders/` and a YAML file with the same `name`.

For example, a funder profile for a `funderxyz` would have a YAML file at `./data/funders/funderxyz/funderxyz.yaml` and might contain the following:

```
version: 1
name: funderxyz
type: Foundation
display_name: Funder XYZ
grant_pools:
  - name: grants-round-1
  - name: grants-round-2
```

## Exploring Funding Data

---

You can read or copy the latest version of the funding data directly from the [oss-funding](https://github.com/opensource-observer/oss-funding) repo.

If you do something cool with the data (eg, a visualization or analysis), please share it with us!
