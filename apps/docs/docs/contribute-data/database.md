---
title: Replicate your SQL Database
sidebar_position: 3
---

OSO's Dagster infrastructure has support for database replication into our data
warehouse by using Dagster's "embedded-elt" that integrates with the library
[dlt](https://dlthub.com/).

## Configure your database as a Dagster asset

There are many possible ways to configure a database as a Dagster asset.
To simplify things, we have built a factory function, `sql_assets`,
to automatically replicate any SQL database.
The SQL database _must_ be a database that is
[supported by dlt](https://dlthub.com/devel/dlt-ecosystem/verified-sources/sql_database).
In general, we replicate _all_ columns and for now custom column selection is not
available in our interface.

This section shows how to replciate 2 tables in a database.
The first table named `some_incremental_database` has a time column
and can be loaded incrementally.
The second table, `some_nonincremental_database`, does not have a way to be loaded
incrementally and will force a full refresh upon every sync.

To setup this database replication, you can add a new python file to
`warehouse/oso_dagster/assets`. This file will have the following contents:

```python
from oso_dagster.factories.sql import sql_assets
from oso_dagster.utils.secrets import SecretReference
from dlt.sources import incremental

my_database = sql_assets(
    "my_database", # The asset prefix for this asset. This is the top level name of the asset.
                # You can think of this as the folder for the asset in the dagster UI

    SecretReference(
        group_name="my_group",     # In most cases this should match the asset prefix
        key="db_connection_string" # A name you'd like to use for the secret.
    ),
    [
        {
            "table": "some_time_series_database",
            "incremental": incremental("time")
        },
        {
            "table": "some_non_time_series_database",
        },
    ],
)
```

The first three lines of the file import some necessary tooling to configure a
SQL database:

- `sql_assets`: an asset factory created by the OSO team
  that enables this simple configuration of SQL assets.
- `SecretReference`: a secret reference in the OSO a secret resolver.
  The secret resolver can be configured differently based on
  the environment. On production, we use a cloud-based secret manager.
- `incremental`: used to specify a column to use for incremental loading.
  This is a `dlt` constructor that is passed to the configuration.

The `sql_assets` factory takes 3 arguments:

- The first argument is an asset key prefix, used to group assets generated
  by the factory. In general, this should match the filename of the python
  file unless you have more complex requirements.
- The second argument must be a `SecretReference` object that will be used to
  retrieve the credentials that you will provide at a later step to the OSO
  team. The `SecretReference` object has two required keyword arguments:

  - `group_name` - Generally this should be the same as the asset key prefix.
    This is an organizational key for the secret manager to use when locating
    the secrets.
  - `key` - This is an arbitrary name for the secret.

- The third argument is a list of dictionaries that define options for tables
  that should be replicated into OSO.

  - `table` - The source table name
  - `destination_table_name` - The destination table name to use in the OSO data lake
  - `incremental` - An `incremental` object that defines time/date based column
    to use for incrementally loading a database.

  Other options exist but full documentation is out of scope for this guide. For
  more information, see the `sql_table` function inside the python package
  located at `warehouse/oso_dagster/dlt_sources/sql_database` of the repository.

## Enabling access to your database

For the asset to run in OSO production, we will need access to
your secrets (e.g. password or connection string).
At this time there is no automated process for this.
You can contact the OSO team on our
[Discord](https://www.opensource.observer/discord).
Be prepared to provide credentials via a secure method of transmission.
Also remember to update any firewall settings that may be required for us
to access your database server.
