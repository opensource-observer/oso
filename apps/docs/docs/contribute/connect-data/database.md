---
title: Replicate a Database
sidebar_position: 2
---

import NextSteps from "./dagster-config.mdx"

OSO's dagster infrastructure has support for database replication into our data
warehouse by using Dagster's "embedded-elt" that integrates with the library
[dlt](https://dlthub.com/).

## Configure your database as a dagster asset

There are many possible ways to configure a database as a dagster asset,
however, to reduce complexity of configuration we provide a single interface for
specifying a SQL database for replication. The SQL database _must_ be a database
that is [supported by
dlt](https://dlthub.com/devel/dlt-ecosystem/verified-sources/sql_database). In
general, we replicate _all_ columns and for now custom column selection is not
available in our interface.

This section shows how to setup a database with two tables as a set of sql
assets. The table named `some_incremental_database` has a chronologically
organized or updated dataset and can therefore be loaded incrementally. The
second table, `some_nonincremental_database`, does not have a way to be loaded
incrementally and will force a full refresh upon every sync.

```python
from oso_dagster.factories.sql import sql_assets
from oso_dagster.utils.secrets import SecretReference
from dlt.sources import incremental

my_database = sql_assets(
    "database",
    SecretReference(group_name="my_group", key="db_connection_string"),
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
sql database. The first import, `sql_assets`, is an asset factory created by the
OSO team that enables this "easy" configuration of sql assets. The second
import, `SecretReference`, is a tool used to reference a secret in a secret
resolver. The secret resolver can be configured differently based on the
environment, but on production we use this to reference a cloud based secret
manager. The final import, `incremental`, is used to specify a column to use for
incremental loading. This is a `dlt` constructor that is passed to the
configuration.

## Enabling access to your database

Before the OSO infrastructure can begin to synchronize your database to the data
warehouse, it will need to be provided access to the database. At this time
there is no automated process for this. Once you're ready to get your database
integrated, you will want to contact the OSO team on our
[Discord](https://www.opensource.observer/discord). Be prepared to provide
credentials (we will work out a secure method of transmission) and also ensure
that you have access to update any firewall settings that may be required for us
to access your database server.

<NextSteps components={props.components}/>
