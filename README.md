# oso [![License: Apache 2.0][license-badge]][license] [![Github Actions][gha-badge]][gha]

[license]: https://opensource.org/license/apache-2-0/
[license-badge]: https://img.shields.io/badge/License-Apache2.0-blue.svg
[gha]: https://github.com/opensource-observer/oso/actions/workflows/ci-default.yml
[gha-badge]: https://github.com/opensource-observer/oso/actions/workflows/ci-default.yml/badge.svg

Open Source Observer is a free analytics suite that helps funders measure the impact of open source software contributions to the health of their ecosystem. TEST STRING

[opensource.observer](https://www.opensource.observer)

## Organization

- `/apps`: The OSO apps
  - `/docs`: documentation (Docusaurus)
    - [on Vercel](https://www.opensource.observer/docs) - Production build
  - `/frontend`: frontend application (Next.js)
    - [on Vercel](https://www.opensource.observer) - Production build
  - `/hasura`: API service (Hasura) - Production
- `/docker`: Docker files
- `/lib`: Common libraries
  - `/oss-artifact-validators`: Simple library to validate different properties of an "artifact"
- `/warehouse`: All code specific to the data warehouse
  - `/dbt`: dbt configuration
  - `/oso_dagster`: Dagster configuration for orchestrating software-defined assets
  - `/oso_lets_go`: Utility for setting up dbt with Google Cloud
  - Also contains other tools to manage warehouse pipelines
- `/ops`: Our ops related code
  - `/external-prs`: GitHub app for validating pull requests
  - `/k8s-*`: Kubernetes configuration
  - `/tf-modules`: Terraform modules

## Quickstart

### System Prequisites

Before you begin you'll need the following on your system:

- Node >= 20 (we suggest installing with [nvm](https://github.com/nvm-sh/nvm))
- pnpm >= 9 (see [here](https://pnpm.io/installation))
- Python >=3.11 (see [here](https://www.python.org/downloads/))
- Python Poetry >= 1.8 (see [here](https://pypi.org/project/poetry/))
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
poetry install
```

You will also need to setup `dbt` to connect to Google BigQuery for running the data pipeline. The following wizard will copy a small playground dataset to your personal Google account and setup `dbt` for you.

```bash
poetry run oso_lets_go
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

### Using the poetry environment

Once installation has completed you can enter the poetry environment.

```bash
$ poetry shell
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

You'll need the path to your poetry environment, which you can get by running

```bash
poetry env info --path
```

Then in VS Code:

- Install the extension
- Open the command pallet, enter "Python: select interpreter"
- Select "Enter interpreter path..."
- Enter the path from the poetry command above

Check that you have a little check mark next to "dbt" in the bottom bar.

### Running dbt

Once you've updated any models you can run dbt _within the poetry environment_ by simply calling:

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

## Reference Playbooks

For setup and common operations for each subproject, navigate into the respective directory and check out the `README.md`.

You can also find some operations guides on our [documentation](https://docs.opensource.observer/docs/how-oso-works/ops/).

## License

The code and documentation in this repository
is released under Apache 2.0
(see [LICENSE](./LICENSE)).

This repository does not contain data.
Datasets may include material that may be subject to third party rights.
For details on each dataset, see
the [Data Overview](https://docs.opensource.observer/docs/integrate/overview/).
