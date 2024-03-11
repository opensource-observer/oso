---
title: Propose an Impact Model
sidebar_position: 5
---

:::info
[dbt (data build tool)](https://www.getdbt.com/blog/what-exactly-is-dbt) is a
command line tool that enables data analysts and engineers to transform data in
the OSO data warehouse more effectively. dbt transforms are written in SQL. We
use them most often to define impact metrics and materialize aggregate data
about projects. You can contribute dbt transforms to create new impact metrics
in our data warehouse.
:::

OSO uses dbt to analyze the data in our public data warehouse on BigQuery. This
is all maintained within the [OSO monorepo][oso] and is open for contribution
from the community.

This guide will walk you through adding a dbt model to the repository.

[oso]: https://github.com/opensource-observer/oso
[oss-directory]: https://github.com/opensource-observer/oss-directory

## Getting Started with dbt

### Prerequisites

Before you begin you'll need the following

- Python 3.11 or higher
- Python Poetry
- git
- A GitHub account
- A basic understanding of dbt and SQL
- While not strictly required, if you'd like to test the models on your own and
  also do any exploratory queries, you'll need a GCP account. This is possible
  by simply having a Google account and logging into the [GCP
  console](https://console.cloud.google.com). If you would like to mostly query
  our views, it is possible to stay under the 1TB free tier per month.

### Fork and clone the repo

Once you've got everything you need to begin, you'll need to fork the [oso
repository](https://github.com/opensource-observer/oso) and clone it to your
local system.

This would look something like:

```bash
git clone git@github.com:your-github-username-here/oso.git
```

### Using the poetry environment locally

From inside the root of the repository, run poetry to install the dependencies.

```bash
$ poetry install
```

Once installation has completed you can enter the poetry environment.

```bash
$ poetry shell
```

From here you should have dbt on your path.

```bash
$ which dbt
```

_This should return something like `opensource-observer/oso/.venv/bin/dbt`_

### Authenticating to BigQuery

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

Finally, authenticate to Google by runnin the following:

```bash
$ gcloud auth application-default login
```

A browser window will pop up after this, so be sure to come back to the docs after you've completed the
login.

You'll need to re-authenticate once an hour. This is simplest to setup but can be a pain
as you need to regularly re-auth. If you need longer access you can setup a
service-account in GCP, but these docs will not cover that for now.

You should now be logged into BigQuery!

### Testing

Test that everything is working by running the following command _within the
poetry environment_:

```bash
$ dbt run --select projects
```

If the command executes properly, then you're ready to start creating your own
dbt models!

## Working with OSO dbt Models

---

### How OSO dbt models are organized

From the root of the oso repository, dbt models can be found at
`warehouse/dbt/models`.

OSO's repository organizes dbt models following the suggested directory
structure from DBT's own best practices guides ([see
here for a fuller explanation](https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview))

- `staging` - This directory contains models used to clean up source data.
  Unless cost prohitibitive, all of these models should be materialized as
  views. Subdirectories within `staging` are organized by the source data.
- `intermediate` - This directory contains models that transform staging data
  into useful representations of the raw warehouse data. These representations
  are not generally intended to be materialized as tables but instead as views.
- `marts` - This directory contains transformations that should be fairly
  minimal and mostly be aggregations. In general, `marts` shouldn't depend on
  other marts unless they're just coarser grained aggregations of an upstream
  mart. Marts are also automatically copied to the postgresql database that runs
  the OSO website.

### OSO data sources

The titles for these sections reflect the directories available in
the `staging` directory of our dbt models.

This isn't an exhaustive list of all data sources but instead a list of data
sources that OSO currently relies upon. If you wish to use other available
public datsets on bigquery. Please feel free to add a model that references that
data source!

#### The `oso_source` macro

For referencing sources, you should use the `oso_source()` macro which has the
same parameters as the built in `source()` macro from DBT. However, the
`oso_source()` macro includes logic that is used to help manage our public
playground dataset.

#### The `oss-directory` source

The OSO community maintains a directory of collections and projects called
[oss-directory][oss-directory].
Additionally, we use the list of project's repositories to gather additional
information on each repository from github. The source data is referenced as `{{
oso_source('ossd', '{TABLE_NAME}') }}` where `{TABLE_NAME}` could be one of the
following tables:

- `collections` - This data is pulled directly from the [oss-directory
  Repository][oss-directory] and is
  groups of projects. You can view this table
  [here][collections_table]
- `projects` - This data is also pulled directly from the oss-directory
  Repository. It describes a project's repositories, blockchain addresses, and
  public packages. You can view this table
  [here][projects_table]
- `repositories` - This data is derived by gathering repository data of all the
  unique repositories present within the `projects` table. You can view this
  table [here][repositories_table]

[collections_table]: https://console.cloud.google.com/bigquery?project=opensource-observer&ws=!1m5!1m4!4m3!1sopensource-observer!2soso!3scollections_ossd
[projects_table]: https://console.cloud.google.com/bigquery?project=opensource-observer&ws=!1m5!1m4!4m3!1sopensource-observer!2soso!3sprojects_ossd
[repositories_table]: https://console.cloud.google.com/bigquery?project=opensource-observer&ws=!1m5!1m4!4m3!1sopensource-observer!2soso!3srepositories_ossd

#### The `github_archive` source

Referenced as `{{ source('github_archive', 'events') }}`, this data source is an
external BigQuery dataset that is maintained by [GH Archive][gharchive]. It is
not suggest that you use this data source directly as doing so can be cost
prohibitive. We would, instead, suggest that you use `{{
ref('stg_github__events') }}` as this is the raw github archive data only for
the projects within the [oss-directory][oss-directory].

For more information we on the GH Archive and what you might find in the raw
data, we suggest you read more at [GH Archive][gharchive]

[gharchive]: https://www.gharchive.org

#### The `dune` source

In order to have collected blockchain data, the OSO team has used dune in the
past (we may not continue to use so into the future) to collect blockchain
transaction and trace data related to the projects in oss-directory. Currently,
the only data available in this dataset is `arbitrum` related transactions and
traces. That collected data is available as a data source that can be referenced
as `{{ oso_source('dune', 'arbitrum') }}`. We also have Optimism data, but that is
currently an export from our legacy data collection. We will expose that as well,
so check back soon for more updates!

### A note about `_id`'s

Due to the diversity of data sources and event types, the ID system used by the
data warehouse might not be immediately obvious to anyone who's starting their
journey with the OSO dbt models.

As a general rule for our dataset, anything that is in the `marts` directory
should that has an ID should generate the ID using the `oso_id()` macro. This
macro generates a url safe base64 encoded identifier from a hash of the
namespace of the identifier and the ID within that namespace. This is done to
simplify some table joins at later stages (so you don't need to match on
multiple dimensions). An example of using the macro within the `collections`
namespace for a collection of the slug `foo` would be as follows:

```jinja
{{ oso_id('collection', 'foo')}}
```

### Special convenience for artifact IDs

There is also an additional convenience macro `oso_artifact_id()` that is used
specifically when dealing with artifacts. This macro automatically converts
columns in a table that contains `artifact` data into an ID by searching along a
specified prefix string for the column names. Specifically, the artifact table
needs to have `namespace`, `type`, and `source_id` to be able to derive a proper
artifact ID. So assuming you have a table that has the namespace prefix with
`foo_` so that we have the columns `foo_namespace`, `foo_type`, and
`foo_source_id` we would use the `artifact_id()` macro like so:

```jinja
{{ oso_artifact_id('foo') }}
```

You can also pass in a table alias by specifying it as the second parameter to
the `oso_artifact_id()` macro:

So assuming you had a SQL select query for a table aliased with `f` that
contains the `foo_` prefixed artifact columns, you could do this:

```jinja
SELECT
  {{ oso_artifact_id('foo', 'f')}} as `artifact_id`
FROM foo_table as f
```

This will return a query of a single column `artifact_id` that is derived from
the `foo_namespace`, `foo_type`, and `foo_source_id` of that table.

## Adding Your dbt Model

---

Now you're armed with enough information to add your model! Add your model to
the directory you deem fitting. Don't be afraid of getting it wrong, that's all
part of our review process to guide you to the right place.

Your model can be written in SQL. We've included some examples to help you get started.

### Running your model

Once you've updated any models you can run dbt _within the poetry environment_ by simply calling:

```bash
$ dbt run
```

_Note: If you configured the dbt profile as shown in this document, this `dbt
run` will write to the `opensource-observer.oso_playground` dataset._

It is likely best to target a specific model so things don't take so long on some of our materializations:

```
$ dbt run --select {name_of_your_model}
```

### Using the BigQuery UI to check your queries

During your development process, it may be useful to use the BigQuery UI to
execute queries.

In the future we will have a way to connect your own
infrastructure so you can generate models from our staging repository. However,
for now, it is best to compile the dbt models into their resulting BigQuery SQL
and execute that on the BigQuery UI. To do this, you'll need to run `dbt
compile` from the root of the [oso Repository][oso] like so:

```bash
$ dbt compile
```

_You'll want to make sure you're also in the `poetry shell` otherwise you won't
use the right dbt binary_

Once you've done so you will be able to find your model compiled in the
`target/` directory (this is in the root of the repository). Your model's
compiled sql can be found in the same relative path as it's location in
`warehouse/dbt/models` inside the `target/` directory.

The presence of the compiled model does not necessarily mean your SQL will work
simply that it was rendered by `dbt` correctly. To test your model it's likely
cheapest to copy the query into the [BigQuery
Console](https://console.cloud.google.com/bigquery) and run that query there. However, if you need more
validation you'll need to [Setup GCP with your own
playground](https://docs.opensource.observer/docs/contribute/transform/setting-up-gcp.md#setting-up-your-own-playground-copy-of-the-dataset)

### Submit a PR

Once you've developed your model and you feel comfortable that it will properly
run. you can submit it a PR to the [oso Repository][oso] to be tested by the OSO
github CI workflows (_still under development_).

### DBT model execution schedule

After your PR has been approved and merged, it will automatically be deployed
into our BigQuery dataset and available for querying. At this time, the data
pipelines are executed once a day by the OSO CI at 02:00 UTC. The pipeline
currently takes a number of hours and any materializations or views would likely
be ready for use by 4-6 hours after that time.

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
LEFT JOIN metrics_all_time AS ma ON p.project_id = ma.project_id
LEFT JOIN metrics_6_months AS m6 on p.project_id = m6.project_id
LEFT JOIN new_users AS nu on p.project_id = nu.project_id
LEFT JOIN user_segments AS us on p.project_id = us.project_id
LEFT JOIN contracts AS c on p.project_id = c.project_id
```
