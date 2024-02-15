---
title: Create Impact Metrics
sidebar_position: 3
---

Write dbt transforms to create new impact metrics in our data warehouse.

[dbt (data build tool)](https://www.getdbt.com/blog/what-exactly-is-dbt) is a command line tool that enables data analysts and engineers to transform data in the OSO data warehouse more effectively. dbt transforms are written in SQL. We use them most often to define impact metrics and materialize aggregate data about projects.

:::warning
At this time the dataset isn't public. This will change in the near future.
:::

## Setting up

---

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

_This should return something like `opensource-observer/oso/.venv/bin/dbt`_

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

---

Once you've updated any models you can run dbt _within the poetry environment_ by simply calling:

```bash
$ dbt run
```

It is likely best to target a specific model so things don't take so long on some of our materializations:

```
$ dbt run --select {name_of_the_model}
```

## Model Examples

---

Here are a few examples of dbt models currently in production:

### Developers

```sql
SELECT
  e.project_slug,
  e.from_source_id,
  e.from_namespace,
  e.from_type,
  TIMESTAMP_TRUNC(e.time, MONTH) AS bucket_month,
  CASE
    WHEN COUNT(DISTINCT CASE WHEN e.type = 'COMMIT_CODE' THEN e.time END) >= 10 THEN 'FULL_TIME_DEV'
    WHEN COUNT(DISTINCT CASE WHEN e.type = 'COMMIT_CODE' THEN e.time END) >= 1 THEN 'PART_TIME_DEV'
    ELSE 'OTHER_CONTRIBUTOR'
  END AS segment_type,
  1 AS amount
FROM {{ ref('int_events_to_project') }} as e
WHERE
  e.type IN (
    'PULL_REQUEST_CREATED',
    'PULL_REQUEST_MERGED',
    'COMMIT_CODE',
    'ISSUE_CLOSED',
    'ISSUE_CREATED'
  )
GROUP BY
  project_slug,
  from_source_id,
  from_namespace,
  from_type,
  bucket_month
```

### Events to a Project

```sql
{#
  All events to a project
#}

SELECT
  a.project_slug,
  e.time,
  e.type,
  a.name as `to_name`,
  e.to_namespace,
  e.to_type,
  e.to_source_id,
  e.from_name,
  e.from_namespace,
  e.from_type,
  e.from_source_id,
  e.amount
FROM {{ ref('int_events') }} AS e
JOIN {{ ref('stg_ossd__artifacts_to_project') }} AS a
  ON a.source_id = e.to_source_id
    AND a.namespace = e.to_namespace
    AND a.type = e.to_type
```
