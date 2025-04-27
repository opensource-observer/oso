# oso [![License: Apache 2.0][license-badge]][license] [![Github Actions][gha-badge]][gha]

[license]: https://opensource.org/license/apache-2-0/
[license-badge]: https://img.shields.io/badge/License-Apache2.0-blue.svg
[gha]: https://github.com/opensource-observer/oso/actions/workflows/ci-default.yml
[gha-badge]: https://github.com/opensource-observer/oso/actions/workflows/ci-default.yml/badge.svg

Open Source Observer is a free analytics suite that helps funders measure the impact of open source software contributions to the health of their ecosystem.

[opensource.observer](https://www.opensource.observer)

## Organization

- `/apps`: The OSO apps
  - `/docs`: documentation (Docusaurus)
    - [on Cloudflare](https://docs.opensource.observer/) - Production build
  - `/frontend`: frontend application (Next.js)
    - [on Vercel](https://www.opensource.observer) - Production build
  - `/hasura-clickhouse`: API service (Hasura+Clickhouse) - Production
  - `/hasura-trino`: API service (Hasura+Trino) - Production
- `/docker`: Docker files
- `/lib`: Common libraries
  - `/oss-artifact-validators`: Simple library to validate different properties of an "artifact"
  - `/utils` - Common TypeScript utilities used in the monorepo
- `/ops`: Our ops related code
  - `/external-prs`: GitHub app for validating pull requests
  - `/help-charts`: Helm charts for Kubernetes
  - `/k8s-*`: Kubernetes configuration
  - `/kind`: Local Kind configuration
  - `/opsscripts`: Python module of various ops related tools
  - `/tf-modules`: Terraform modules
- `/warehouse`: All code specific to the data warehouse
  - `/dbt`: dbt configuration
  - `/docker`: Docker configuration
  - `/metrics_tools`: Python utilities for managing data
  - `/oso_agent`: OSO agent
  - `/oso_dagster`: Dagster configuration for orchestrating software-defined assets
  - `/oso_sqlmesh`: sqlmesh configuration
  - `/pyoso`: Python package for `pyoso`
  - Also contains other tools to manage warehouse pipelines

## Quickstart

### System Prerequisites

Before you begin you'll need the following on your system:

- Node >= 20 (we suggest installing with [nvm](https://github.com/nvm-sh/nvm))
- pnpm >= 9 (see [here](https://pnpm.io/installation))
- Python >=3.11 (see [here](https://www.python.org/downloads/))
- Python uv >= 0.6 (see [here](https://pypi.org/project/uv/))
- git (see [here](https://github.com/git-guides/install-git))

### Setup dependencies

To install Node.js dependencies

```
pnpm install
```

Also install the python dependencies

```
uv sync --all-packages
```

## Reference Playbooks

For setup and common operations for each subproject, navigate into the respective directory and check out the `README.md`.

You can also find some operations guides on our [documentation](https://docs.opensource.observer/docs/guides/ops/).

## License

The code and documentation in this repository
is released under Apache 2.0
(see [LICENSE](./LICENSE)).

This repository does not contain data.
Datasets may include material that may be subject to third party rights.
For details on each dataset, see
the [Data Overview](https://docs.opensource.observer/docs/integrate/datasets/).
