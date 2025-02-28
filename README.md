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
    - [on Vercel](https://docs.opensource.observer/docs) - Production build
  - `/frontend`: frontend application (Next.js)
    - [on Vercel](https://www.opensource.observer) - Production build
  - `/hasura`: API service (Hasura) - Production
- `/cli`: The `oso` cli for setting up and using various tools in this repository
- `/docker`: Docker files
- `/lib`: Common libraries
  - `/oss-artifact-validators`: Simple library to validate different properties of an "artifact"
  - `/oso_common` - Python module for common tools across all python tools
- `/warehouse`: All code specific to the data warehouse
  - `/dbt`: dbt configuration
  - `/oso_dagster`: Dagster configuration for orchestrating software-defined assets
  - `/metrics_mesh`: sqlmesh configuration
  - Also contains other tools to manage warehouse pipelines
- `/ops`: Our ops related code
  - `/external-prs`: GitHub app for validating pull requests
  - `/k8s-*`: Kubernetes configuration
  - `/tf-modules`: Terraform modules
  - `/opstools`: Python module of various ops related tools

## Quickstart

### System Prerequisites

Before you begin you'll need the following on your system:

- Node >= 20 (we suggest installing with [nvm](https://github.com/nvm-sh/nvm))
- pnpm >= 9 (see [here](https://pnpm.io/installation))
- Python >=3.11 (see [here](https://www.python.org/downloads/))
- Python uv >= 0.6 (see [here](https://pypi.org/project/uv/))
- git (see [here](https://github.com/git-guides/install-git))
- BigQuery access (see [here](https://docs.opensource.observer/docs/get-started/#login-to-bigquery) if you don't have it setup already)
- gcloud (see [here](https://cloud.google.com/sdk/docs/install))

### Setup dependencies

First, authenticate with `gcloud`:

```bash
gcloud auth application-default login
```

Then install Node.js dependencies

```
pnpm install
```

Also install the python dependencies

```
uv sync
```

You will also need to setup `dbt` to connect to Google BigQuery for running the data pipeline. The following wizard will copy a small playground dataset to your personal Google account and setup `dbt` for you.

```bash
uv run oso lets_go
```

:::tip
The script is idempotent, so you can safely run it again
if you encounter any issues.
:::

## Frontend Development

### Setup and build the frontend

First, make sure the environment variables are set for `./apps/frontend`.
Take a look at `./apps/frontend/.env.local.example` for the complete list.

- You can either set these yourself (e.g. in CI/CD)
- or copy the file to `.env.local` and populate it.

Then do a turbo build of all apps, run the following:

```bash
pnpm install
pnpm build
```

The resulting static site can be found in `./build/`.

### Running the prod server

If you've already run the build, you can use `pnpm serve` to serve the built files

### Running the frontend dev server

To run a dev server that watches for changes across code and Plasmic, run:

```bash
pnpm dev:frontend
```

## dbt Development

Our datasets are public! If you'd like to use them directly as opposed to adding to our
dbt models, checkout [our docs!](https://docs.opensource.observer/docs/get-started/)

### Using the virtual environment

Once installation has completed you can enter the virtual environment.

```bash
$ source .venv/bin/activate
```

From here you should have dbt on your path.

```bash
$ which dbt
```

_This should return something like `opensource-observer/oso/.venv/bin/dbt`_

### Authenticating to bigquery

If you have write access to the dataset then you can connect to it by setting
the `opensource_observer` profile in `dbt`. Inside `~/.dbt/profiles.yml` (create
it if it isn't there), add the following:

```yaml
opensource_observer:
  outputs:
    production:
      type: bigquery
      dataset: oso
      job_execution_time_seconds: 300
      job_retries: 1
      location: US
      method: oauth
      project: opensource-observer
      threads: 32
    playground:
      type: bigquery
      dataset: oso_playground
      job_execution_time_seconds: 300
      job_retries: 1
      location: US
      method: oauth
      project: opensource-observer
      threads: 32
  # By default we target the playground. it's less costly and also safer to write
  # there while developing
  target: playground
```

### Setting up VS Code

The [Power User for dbt core](https://marketplace.visualstudio.com/items?itemName=innoverio.vscode-dbt-power-user) extension is pretty helpful.

You'll need the path to your virtual environment, which you can get by running

```bash
echo 'import sys; print(sys.prefix)' | uv run -
```

Then in VS Code:

- Install the extension
- Open the command pallet, enter "Python: select interpreter"
- Select "Enter interpreter path..."
- Enter the path from the uv command above

Check that you have a little check mark next to "dbt" in the bottom bar.

### Running dbt

Once you've updated any models you can run dbt _within the virtual environment_ by simply calling:

```bash
$ dbt run
```

:::tip
Note: If you configured the dbt profile as shown in this document,
this `dbt run` will write to the `opensource-observer.oso_playground` dataset.
:::

It is likely best to target a specific model so things don't take so long on some of our materializations:

```
$ dbt run --select {name_of_the_model}
```

## sqlmesh Development

### Running sqlmesh

For faster development of new models, we rely on duckdb as a local development
environment. While this introduces the need to ensure we have macros to
compensate for differences between environments, the simple deployment allows
for fast iteration of ideas given that the required macros exist.

To get started we need to load localized data:

To do that we do:

```bash
# Ensure we're logged into google
gcloud auth application-default login

# Run the initialization of the data pull
oso local initialize --max-results-per-query 10000 --max-days 3
```

This will download 3 days of time series data with an approximate maximum of
10000 rows in each table that is not time series defined. You can change these
or unset them if you're certain that your system can handle a larger data
download but this will be required.

Once all of the data has been downloaded you can now run sqlmesh like so:

```bash
oso local sqlmesh [...any sqlmesh args...]
```

This is a convenience function for running sqlmesh locally. This is equivalent to running this series of commands:

```bash
cd warehouse/metrics_mesh
sqlmesh [...any sqlmesh args... ]
```

So running:

```bash
oso local sqlmesh plan
```

Would be equivalent to

```bash
cd warehouse/metrics_mesh
sqlmesh plan
```

However, the real reason for this convenience function is for executing sqlmesh
against a local trino as detailed in this next section.

### Running sqlmesh on a local trino

Be warned, running local trino requires running kubernetes on your machine using
[kind](https://kind.sigs.k8s.io/). While it isn't intended to be a heavy weight
implementation, it takes more resources than simply running with duckdb.
However, in order to simulate and test this running against trino as it does on
the production OSO deployment, we need to have things wired properly with kubernetes. To initialize everything simply do:

```bash
oso ops cluster-setup
```

This can take a while so please be patient, but it will generate a local
registry that is used when running the trino deployment with the metrics
calculation service deployed. This is to test that process works and to ensure
that the MCS has the proper version deployed. Eventually this can/will be used
to test the dagster deployment.

Once everything is setup, things should be running in the kind cluster
`oso-local-test-cluster`. Normally, you'd need to ensure that you forward the
right ports so that you can access the cluster to run the sqlmesh jobs but the
convenience functions we created to run sqlmesh ensure that this is done
automatically. However before running sqlmesh you will need to initialize the
data in trino.

Much like running against a local duckdb the local trino can also be initialized with on the CLI like so:

```bash
oso local initialize --local-trino
```

Once completed, trino will be configured to have the proper source data for sqlmesh.

Finally, to run `sqlmesh plan` do this:

```bash
oso local sqlmesh --local-trino plan
```

The `--local-trino` option should be passed before any sqlmesh args. Otherwise, you can call any command or use any flags from sqlmesh after the `sqlmesh` keyword in the command invocation. So to call `sqlmesh run` you'd simply do:

```bash
oso local sqlmesh --local-trino run
```

Please note, you may periodically be logged out of the local kind cluster, just
run `oso ops cluster-setup` again if that happens.

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
