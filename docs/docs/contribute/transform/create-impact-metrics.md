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

:::warning
If you target the `production` dataset you'll be editing the live
production data. Do so with caution if you have write access to these datasets.
:::

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
      threads: 1
    playground:
      type: bigquery
      dataset: oso
      job_execution_time_seconds: 300
      job_retries: 1
      location: US
      method: oauth
      project: opensource-observer
      threads: 1
  # By default we target the playground. it's less costly and also safer to write
  # there while developing
  target: playground
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

_Note: If you configured the dbt profile as shown in this document, this `dbt
run` will write to the `opensource-observer.oso_playground` dataset._

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

### Summary Onchain Metrics by Project

```sql
{#
  Summary onchain metrics for a project on a specific chain
#}

WITH txns AS (
  SELECT
    a.project_id,
    c.from_source_id AS from_id,
    DATE(TIMESTAMP_TRUNC(c.time, MONTH)) AS bucket_month,
    l2_gas,
    tx_count
  FROM {{ ref('stg_dune__CHAIN_contract_invocation') }} AS c -- add the CHAIN namespace here
  JOIN {{ ref('stg_ossd__artifacts_by_project') }} AS a ON c.to_source_id = a.artifact_source_id
),
metrics_all_time AS (
  SELECT
    project_id,
    MIN(bucket_month) AS first_txn_date,
    COUNT (DISTINCT from_id) AS total_users,
    SUM(l2_gas) AS total_l2_gas,
    SUM(tx_count) AS total_txns
  FROM txns
  GROUP BY project_id
),
metrics_6_months AS (
  SELECT
    project_id,
    COUNT (DISTINCT from_id) AS users_6_months,
    SUM(l2_gas) AS l2_gas_6_months,
    SUM(tx_count) AS txns_6_months
  FROM txns
  WHERE bucket_month >= DATE_ADD(CURRENT_DATE(), INTERVAL -6 MONTH)
  GROUP BY project_id
),
new_users AS (
  SELECT
    project_id,
    SUM(is_new_user) AS new_user_count
  FROM (
    SELECT
      project_id,
      from_id,
      CASE WHEN MIN(bucket_month) >= DATE_ADD(CURRENT_DATE(), INTERVAL -3 MONTH) THEN 1 END AS is_new_user
    FROM txns
    GROUP BY project_id, from_id
  )
  GROUP BY project_id
),
user_txns_aggregated AS (
  SELECT
    project_id,
    from_id,
    SUM(tx_count) AS total_tx_count
  FROM txns
  WHERE bucket_month >= DATE_ADD(CURRENT_DATE(), INTERVAL -3 MONTH)
  GROUP BY project_id, from_id
),
multi_project_users AS (
  SELECT
    from_id,
    COUNT(DISTINCT project_id) AS projects_transacted_on
  FROM user_txns_aggregated
  GROUP BY from_id
),
user_segments AS (
  SELECT
    project_id,
    COUNT(DISTINCT CASE WHEN user_segment = 'HIGH_FREQUENCY_USER' THEN from_id END) AS high_frequency_users,
    COUNT(DISTINCT CASE WHEN user_segment = 'MORE_ACTIVE_USER' THEN from_id END) AS more_active_users,
    COUNT(DISTINCT CASE WHEN user_segment = 'LESS_ACTIVE_USER' THEN from_id END) AS less_active_users,
    COUNT(DISTINCT CASE WHEN projects_transacted_on >= 3 THEN from_id END) AS multi_project_users
  FROM (
    SELECT
      uta.project_id,
      uta.from_id,
      CASE
        WHEN uta.total_tx_count >= 1000 THEN 'HIGH_FREQUENCY_USER'
        WHEN uta.total_tx_count >= 10 THEN 'MORE_ACTIVE_USER'
        ELSE 'LESS_ACTIVE_USER'
      END AS user_segment,
      mpu.projects_transacted_on
    FROM user_txns_aggregated AS uta
    JOIN multi_project_users AS mpu ON uta.from_id = mpu.from_id
  )
  GROUP BY project_id
),
contracts AS (
  SELECT
    project_id,
    COUNT(artifact_source_id) AS num_contracts
  FROM {{ ref('stg_ossd__artifacts_by_project') }}
  GROUP BY project_id
)

SELECT
  p.project_id,
  p.project_name,
  c.num_contracts,
  ma.first_txn_date,
  ma.total_txns,
  ma.total_l2_gas,
  ma.total_users,
  m6.txns_6_months,
  m6.l2_gas_6_months,
  m6.users_6_months,
  nu.new_user_count,
  (us.high_frequency_users + us.more_active_users + us.less_active_users) AS active_users,
  us.high_frequency_users,
  us.more_active_users,
  us.less_active_users,
  us.multi_project_users

FROM {{ ref('projects') }} AS p
INNER JOIN metrics_all_time AS ma ON p.project_id = ma.project_id
INNER JOIN metrics_6_months AS m6 on p.project_id = m6.project_id
INNER JOIN new_users AS nu on p.project_id = nu.project_id
INNER JOIN user_segments AS us on p.project_id = us.project_id
INNER JOIN contracts AS c on p.project_id = c.project_id
```
