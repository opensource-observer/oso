---
title: New Contributor Guide
description: Get up to speed with Open Source Observer (OSO) and start contributing effectively
sidebar_position: 20
---

Welcome! This guide will help you get started as a contributor to Open Source Observer (OSO). Follow these steps to set up your development environment and join our community.

## 1. Connect to the OSO Data Lake

Start by exploring OSO's data and understanding what we're building:

1. **Get started with OSO data** - Follow the [Get Started guide](../get-started/index.md) to access our data lake
2. **Complete a tutorial** - Work through at least one [tutorial](../tutorials/index.md) using `pyoso` to understand our data models
3. **Test the API** - Make some test queries to the [OSO API](../get-started/api.mdx) to see what's available

## 2. Set Up Your Local Development Environment

### Install Prerequisites

1. **Install uv** - We use [uv](https://docs.astral.sh/uv/) for Python dependency management
2. **Install duckdb** - We use [duckdb](https://duckdb.org/) for local data exploration

### Clone the core repositories

```bash
git clone https://github.com/opensource-observer/oso.git
git clone https://github.com/opensource-observer/oss-directory.git
```

### Run SQLMesh locally

- **Location**: [`warehouse/oso_sqlmesh`](https://github.com/opensource-observer/oso/tree/main/warehouse/oso_sqlmesh)
- **Guide**: [SQLMesh Quickstart Guide](../contribute-models/sqlmesh/quickstart.md)

You should be able to run a `sqlmesh plan` successfully, eg:

```bash
uv run oso local sqlmesh-test --duckdb plan dev --start '1 week' --end now
```

### Run Dagster locally

- **Location**: [`warehouse/oso_dagster`](https://github.com/opensource-observer/oso/tree/main/warehouse/oso_dagster)
- **Guide**: [Dagster Setup Guide](../guides/dagster.md) and [Dagster Quick Start](../contribute-data/setup/index.md)

You should be able to run `uv run dagster dev` successfully.

4. **Run the Docs locally**

- **Location**: [`apps/docs`](https://github.com/opensource-observer/oso/tree/main/apps/docs)

You should be able to run `pnpm start` successfully.

### Run OSS Directory validation locally

- **Location**: [oss-directory](https://github.com/opensource-observer/oss-directory)
- **Guide**: [OSS Directory Guide](../guides/oss-directory/index.md)

You should be able to run `pnpm validate` successfully.

## 3. Join the Community

### Connect with the Team

1. **Join Discord** - [OSO Discord Server](https://www.opensource.observer/discord)
   - Introduce yourself in the `#lobby` channel with:
     - Your name / GitHub profile
     - Brief background
     - What you'd like to work on
2. **Join Gather** - [OSO Gather Space](https://www.opensource.observer/gather)
   - Recommended if you plan to contribute 10+ hours per week

### Daily Stand-up

- **Time**: 16:00 UTC on Gather
- **Purpose**: Share progress, unblock issues, stay connected

### Find Work

1. **Browse open issues** - [Help Wanted Issues](https://github.com/opensource-observer/oso/issues?q=is%3Aopen+label%3A%22help+wanted%22)
2. **Check project board** - [OSO Project Board](https://github.com/opensource-observer/oso/projects)
3. **Comment on issues** to claim them before starting work

## 4. Contribution Workflow

### Development Process

1. **Fork and branch** - Create a feature branch from `main`
2. **Follow CI standards**:
   - Run hooks and local build tests
   - For data models: run `sqlmesh plan` and ensure tests pass
   - For Dagster jobs: verify the materialization is successful locally
3. **Update documentation** - Modify docs in `apps/docs` when adding/changing functionality
4. **Submit PR** - Link to relevant issues and request reviews

### Code Quality

- Follow the existing code style and patterns
- Update documentation to include any new functionality (or issues you encountered in any of the workflows)
- Ensure all CI checks pass before requesting review

## 5. Getting Help

- **Discord**: Ask questions in channel
- **GitHub**: Tag maintainers on issues or PRs
- **Documentation**: Check our [guides](../guides/index.mdx) and [references](../references/index.mdx)

---

We're excited to have you join the OSO community! This is a collaborative effort to measure the impact of open source software, and your contributions help make it possible.
