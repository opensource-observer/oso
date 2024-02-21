---
title: Adding DBT Models
sidebar_position: 6
---

OSO uses dbt to analyze the data in our public data warehouse on BigQuery. This
is all maintained within the [oso
repository](https://github.com/opensource-observer/oso) and is open for
contribution from the community. This guide will walk you through adding a DBT
model to the repository.

## Prerequisites

Before you begin you'll need the following

- Python 3.11 or higher
- Python Poetry
- git
- A github account
- A basic understanding of dbt and SQL
- If you'd like to test the models on your own, you'll also need a GCP account

## Fork and clone the repo

Once you've got everything you need to begin, you'll need to fork the [oso
repository](https://github.com/opensource-observer/oso) and clone it to your
local system.

This would look something like:

```bash
git clone git@github.com:your-github-username-here/oso.git
```

## Installing tools locally

From inside the root of the repository, run poetry to install the dependencies.

```bash
$ poetry install
```

## Using the poetry environment

Once installation has completed you can enter the poetry environment.

```bash
$ poetry shell
```

From here you should have dbt on your path.

```bash
$ which dbt
```

_This should return something like `opensource-observer/oso/.venv/bin/dbt`_

## Locating the dbt models

From the root of the oso repository, dbt models can be found at `dbt/models`.

## How OSO dbt models are organized

OSO's repository organizes dbt models following the suggested directory
structure from DBT's own best practices guides ([see
here for a fuller explanation](https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview))

- `staging` - This subdirectory contains models used to clean up source data.
  Unless cost prohitibitive, all of these models should be materialized as
  views.
- `intermediate` - This subdirectory contains models that transform staging data
  into useful representations of the raw warehouse data. These representations
  are not generally intended to be materialized as tables but instead as views.
- `marts` - This subdirectory contains transformations that should be fairly
  minimal and mostly be aggregations. In general, `marts` shouldn't depend on
  other marts unless they're just coarser grained aggregations of an upstream
  mart. Marts are also automatically copied to the postgresql database that runs
  the OSO website.

## Add your model!

Now you're armed with enough information to add your model! Add your model to
the directory you deem fitting. Don't be afraid of getting it wrong, that's all
part of our review process to guide you to the right place. Once you've
developed your model you can either choose to test it on your own infrastructure
or you can submit it as a PR to be tested by the OSO github CI workflows
(_still under development_)

## Connecting to OSO's staging environment

_WARNING: This will incur costs on your GCP account_

If you wish to test your model on your own GCP. You can utilize our staging data warehouse as the source data for dbt models in your own GCP account.

...tbd

## Submit a PR

Once you feel you've completed your model, submit a PR to the OSO repository.

## DBT model execution schedule

After your PR has been accepted it will automatically be deployed into our data
warehouse and available for querying. At this time, the data pipelines are
executed once a day by the OSO CI at 02:00 UTC. The pipeline currently takes a
number of hours and any materializations or views would likely be ready for use
by 4-6 hours after that time.
