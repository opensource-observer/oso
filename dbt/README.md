# oso dbt

_At this time the dataset isn't public. This will change in the near future._

## Setting up

### Prequisites

- Python 3 (Tested on 3.11)
- [poetry](https://python-poetry.org/)
  - Install with pip: `pip install poetry`

### Install dependencies

From inside the `dbt` directory, run poetry to install the dependencies.

```bash
$ poetry install
```

### Using the poetry environment

Once installation has completed you can enter the poetry environment.

```bash
$ poetry shell
```

From here you should have dbt on your path.

```bash
$ which dbt
```

_This should return something like `opensource-observer/oso/dbt/.venv/bin/dbt`_

### Authenticating to bigquery

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

For now we have to set some environment variables before we run the models. These
are related to the github events from gharchive. So you'll need to set two 
variables:

* `GITHUB_ARCHIVE_PARTITION_TYPE` - This can be `year`, `month`, `day`. If you're
  only testing it's suggested to use `day` because it's costly to query `month` or
  `year` partitions.
* `GITHUB_ARCHIVE_PARTITION_KEY` - This value is the key for the partition type.
    * `YYYY` for `year` partition type
    * `YYYYMM` for `month` partition type
    * `YYYYMMDD` for day partition type

Once you've updated any models you can run dbt _within the poetry environment_
from the `dbt/` directory.

```bash
# This will query gharchive for events from 2023-12-15
$ GITHUB_ARCHIVE_PARTITION_TYPE=day GITHUB_ARCHIVE_PARTITION_KEY=20231215 dbt run
```
