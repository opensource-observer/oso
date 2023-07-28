# oso [![License: Apache 2.0][license-badge]][license] [![Github Actions][gha-badge]][gha]

[license]: https://opensource.org/license/apache-2-0/
[license-badge]: https://img.shields.io/badge/License-Apache2.0-blue.svg
[gha]: https://github.com/hypercerts-org/oso/actions/workflows/ci-default.yml
[gha-badge]: https://github.com/hypercerts-org/oso/actions/workflows/ci-default.yml/badge.svg

Open source observer is a tool for measuring the impact of open source software ecosystems.

[www.opensource.observer](https://www.opensource.observer)

## Organization

- `/docs`: documentation (Docusaurus)
  - [on Vercel](https://www.opensource.observer/docs) - Production build
- `/frontend`: frontend application (Next.js)
  - [on Vercel](https://www.opensource.observer) - Production build
- `/indexer`: Data indexer
  - [on GitHub actions](https://github.com/hypercerts-org/oso/actions/workflows/indexer-autocrawl.yml)

## Quickstart

### Setup and build the frontend

First, make sure the environment variables are set for `./frontend`.
Take a look at `./frontend/.env.local.example` for the complete list.

- You can either set these yourself (e.g. in CI/CD)
- or copy the file to `.env.local` and populate it.

Then the do a turbo build of all apps, run the following:

```bash
yarn install
yarn build
```

The resulting static site can be found in `./build/`.

### Running the prod server

If you've already run the build, you can use `yarn serve` to serve the built files

### Running the frontend dev server

To run a dev server that watches for changes across code and Plasmic, run:

```bash
yarn dev:frontend
```

## Playbooks

For setup and common operations for each subproject, navigate into the respective directory and check out the `README.md`.

We also maintain a [playbook](https://hypercerts.org/docs/devops) for larger operations.
