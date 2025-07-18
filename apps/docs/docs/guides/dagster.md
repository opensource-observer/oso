---
title: Dagster Guide
sidebar_position: 6
---

OSO uses Dagster to perform all data orchestration in our backend infrastructure.
Most of the time, contributors will be working in Dagster to
connect new data sources.
If the source data already exists in OSO, take a look at
[contributing models via sqlmesh](../contribute-models/index.mdx).

In order to setup Dagster in your development environment,
check out the [getting started guide](../contribute-data/setup/index.md).

## Data Architecture

As much as possible, we store data in an Iceberg cluster,
making it the center of gravity of the OSO data lake.
Thus, data ingest will typically go into Iceberg tables.
[`pyoso`](../get-started/python.md) is the best way to query any data in these tables.
This will make it significantly easier to decentralize OSO infrastructure
in the future.

## Job schedules

All automated job schedules can be found on our public
[Dagster dashboard](https://dagster.opensource.observer/automation).

Currently, our main data pipeline runs once per week on Sundays.

## Alert system

Dagster alert sensors are configured in
[`warehouse/oso_dagster/factories/alerts.py`](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/factories/alerts.py)

Right now, alerts are reported to `#alerts` in the
[OSO Discord server](https://www.opensource.observer/discord).

## Secrets Management

When you are creating new data sources for OSO,
you may need to handle secrets (e.g. passwords, access keys, DB connection strings).

:::warning
**DO NOT CHECK SECRETS INTO THE REPOSITORY!**
:::

Instead, please use the OSO `SecretResolver` to properly handle your secrets.

### Local secrets

While you are developing your code,
the right place to store secrets is in your root `.env` file.
The OSO `SecretResolver` organizes secrets by
`(prefix, group, key)`.
Dagster will automatically load secrets from your environment by
the following convention `PREFIX__GROUP__KEY`.
By default, all secrets in Dagster use the prefix, `dagster`.

For example, we store all Clickhouse secrets under the `clickhouse` group.
Thus, these are the environment variables we'd set for Clickhouse:

```
DAGSTER__CLICKHOUSE__HOST=
DAGSTER__CLICKHOUSE__USER=
DAGSTER__CLICKHOUSE__PASSWORD=
```

You can reference a secret using `SecretReference`
and resolve it using `SecretResolver`.

```python
from ..utils import SecretReference, SecretResolver

password_ref = SecretReference(group_name="clickhouse", key="password")
password = secret_resolver.resolve_as_str(password_ref)
```

In order to get a reference to the `SecretResolver`,
you'll want to accept it as a Dagster resource.
You can see
[`definitions.py`](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/definitions.py) and
[`clickhouse.py`](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/resources/clickhouse.py) as an example.

### Production secrets

When you are ready to run your assets in production,
please reach out to the core OSO team on
[Discord](https://www.opensource.observer/discord).
We will arrange a secure way to share your secrets
into our production keystore.

### Restating SQLMesh models

:::warning
**DO NOT RESTATE SQLMesh models without approval!**
:::

If you need to restate a SQLMesh model, you can do so via the Dagster UI.

Select the job, e.g., `sqlmesh_all_assets`.

Then select the dropdown menu next to the **Materialize all** button and click **Open launchpad**.

Update the config to include the model you want to restate, for example:

```yaml
ops:
  sqlmesh_project:
    config:
      restate_by_entity_category: false
      restate_models:
        - oso.stg_github__XYZ
        - oso.stg_github__XYZ_2
      skip_tests: false
```

This will restate the `stg_github__XYZ` and `stg_github__XYZ_2` staging models and all downstream SQLMesh models in the warehouse.
