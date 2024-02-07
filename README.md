# oso [![License: Apache 2.0][license-badge]][license] [![Github Actions][gha-badge]][gha]

[license]: https://opensource.org/license/apache-2-0/
[license-badge]: https://img.shields.io/badge/License-Apache2.0-blue.svg
[gha]: https://github.com/opensource-observer/oso/actions/workflows/ci-default.yml
[gha-badge]: https://github.com/opensource-observer/oso/actions/workflows/ci-default.yml/badge.svg

Open Source Observer is a free analytics suite that helps funders measure the impact of open source software contributions to the health of their ecosystem.

[opensource.observer](https://www.opensource.observer)

## Organization

- `/docs`: documentation (Docusaurus)
  - [on Vercel](https://www.opensource.observer/docs) - Production build
- `/frontend`: frontend application (Next.js)
  - [on Vercel](https://www.opensource.observer) - Production build
- `/indexer`: Data indexer
  - [on GitHub actions](https://github.com/opensource-observer/oso/actions/workflows/indexer-autocrawl.yml)

## Frontend Quickstart

### Setup and build the frontend

First, make sure the environment variables are set for `./frontend`.
Take a look at `./frontend/.env.local.example` for the complete list.

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

## Playbooks

For setup and common operations for each subproject, navigate into the respective directory and check out the `README.md`.

## dbt Start

_At this time the dataset isn't public. This will change in the near future._

### Setting up

#### Prequisites

- Python 3 (Tested on 3.11)
- [poetry](https://python-poetry.org/)
  - Install with pip: `pip install poetry`

#### Install dependencies

From inside the `dbt` directory, run poetry to install the dependencies.

```bash
$ poetry install
```

#### Using the poetry environment

Once installation has completed you can enter the poetry environment.

```bash
$ poetry shell
```

From here you should have dbt on your path.

```bash
$ which dbt
```

_This should return something like `opensource-observer/oso/.venv/bin/dbt`_

#### Authenticating to bigquery

If you have write access to the dataset then you can connect to it by setting
the `opensource_observer` profile in `dbt`. Inside `~/.dbt/profiles.yml` (create
it if it isn't there), add the following:

```yaml
opensource_observer:
  outputs:
    dev:
      type: bigquery
      dataset: opensource_observer
      job_execution_time_seconds: 300
      job_retries: 1
      location: US
      method: oauth
      project: oso-production
      threads: 1
  target: dev
```

If you don't have `gcloud` installed you'll need to do so as well. The
instructions are [here](https://cloud.google.com/sdk/docs/install).

_For macOS users_: Instructions can be a bit clunky if you're on macOS, so we
suggest using homebrew like this:

```bash
$ brew install --cask google-cloud-sdk
```

Finally, authenticate to google run the following (a browser window will pop up
after this so be sure to come back to the docs after you've completed the
login):

```bash
$ gcloud auth application-default login
```

You'll need to do this once an hour. This is simplest to setup but can be a pain
as you need to regularly reauth. If you need longer access you can setup a
service-account in GCP, but these docs will not cover that for now.

You should now be logged into BigQuery!

## Usage

Once you've updated any models you can run dbt _within the poetry environment_ by simply calling:

```bash
$ dbt run
```

It is likely best to target a specific model so things don't take so long on some of our materializations:

```
$ dbt run --select {name_of_the_model}
```
