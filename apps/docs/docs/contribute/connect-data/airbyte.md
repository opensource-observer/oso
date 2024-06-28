---
title: 🏗️ Connect via Airbyte
sidebar_position: 7
sidebar_class_name: hidden
---

:::warning
While Dagster does have support for integrating with
[Airbyte](https://docs.dagster.io/integrations/airbyte),
we do not currently run an Airbyte server.
We prefer using Dagster
[embedded-elt](https://docs.dagster.io/_apidocs/libraries/dagster-embedded-elt).
If you have tips on how to run Airbyte plugins within
embedded-elt, please send us a PR!
:::

## Replicating external databases

If your data exists in an off-the-shelf database,
you can replicate data to OSO via an AirByte Connector or
Singer.io Tap integration through Meltano, which is run in a GitHub action.
This configuration does not require running an Airbyte server.

This section provides the details
necessary to add a connector or a tap from an existing Postgres database into
our system. Other databases or datasources should be similar.

### Settings up your Postgres database for connection

We will setup the postgre connection to use Change Data Capture which is
suggested for very large databases. You will need to have the following in order
to connect your postgres database to OSO for replication.

- `wal_level` must be set to `logical`
- You need to create a username of your choosing and share the associated
  credentials with a maintainer at OSO
- You need to grant `REPLICATION` privileges to a username of your choosing
- You need to create a replication slot
- You need to create a publication for OSO for the tables you wish to have replicated.

#### Setting your `wal_level`

:::warning
Please ensure that you understand what changing the `wal_level` will do for your
database system requirements and/or performance.
:::

Before you begin, it's possible your settings are already correct. To check your
`wal_level` settings, run the following query:

```SQL
SHOW wal_level;
```

The output would look something like this from `psql`:

```
 wal_level
-----------
 logical
```

If doesn't have the word `logical` but instead some other value, you will need
to change this. Please ensure that this `wal_level` change is actually what you
want for your database. Setting this value to `logical` will likely affect
performance as it increases the disk writes by the database process. If you are
comfortable with this, then you can change the `wal_level` by executing the
following:

```SQL
ALTER SYSTEM SET wal_level = logical;
```

#### Creating a user for OSO

To create a user, choose a username and password, here we've chosen `oso_user`
and have a placeholder password `somepassword`:

```SQL
CREATE USER oso_user WITH PASSWORD 'somepassword';
```

#### Granting replication privileges

The user we just created will need replication privileges

```SQL
ALTER USER oso_user WITH REPLICATION;
```

#### Create a replication slot

Create a replication slot for the `oso_user`. Here we named it `oso_slot`, but
it can have any name.

```SQL
SELECT * FROM pg_create_logical_replication_slot('oso_slot', 'pgoutput');
```

#### Create a publication

For the final step, we will be creating the publication which will subscribe to
a specific table or tables. That table should already exist. If it does not, you
will need to create it _before_ creating the publication. Once you've ensured
that the table or tables in question have been created, run the following to
create the publication:

_This assumes that you're creating the publication for table1 and table2._

```SQL
CREATE PUBLICATION oso_publication FOR TABLE table1, table2;
```

You can also create a publication for _all_ tables. To do this run the following
query:

```SQL
CREATE PUBLICATION oso_publication FOR ALL TABLES;
```

For more details about this command see: https://www.postgresql.org/docs/current/sql-createpublication.html

### Adding your postgres replication data to the OSO Meltano configuration

In the future we will move everything over to our Dagster setup.
For now, we will run Airbyte plugins via Meltano in a GitHub actions workflow.

#### Add the extractor to `meltano.yml`

The `meltano.yml` YAML file details all of the required configuration for the
meltano "extractors" which are either airbyte connectors or singer.io taps.

For postgres data sources we use the postgres airbyte connector. Underneath the
`extractors:` section. Add the following as a new list item (you should choose a
name other than `tap-my-postgres-datasource`):

```yaml
extractors:
  # ... other items my be above
  # Choose any arbitrary name tap-# that is related to your datasource
  - name: tap-my-postgres-datasource
    inherit_from: tap-postgres
    variant: airbyte
    pip_url: git+https://github.com/MeltanoLabs/tap-airbyte-wrapper.git
    config:
      airbyte_config:
        jdbc_url_params: "replication=postgres"
        ssl_mode: # Update with your SSL configuration
          mode: enable
        schemas: # Update with your schemas
          - public
        replication_method:
          plugin: pgoutput
          method: CDC
          publication: publication_name
          replication_slot: oso_slot
          initial_waiting_seconds: 5
```

#### Send the read only credentials to OSO maintainers

For now, once this is all completed it is best to open a pull request and an OSO
maintainer will reach out with a method to accept the read only credentials.

## Writing a new Airbyte connector

Airbyte provides one of the best ways to write data connectors
that ingest data from HTTP APIs and other Python sources via the
[Airbyte Python CDK](https://docs.airbyte.com/connector-development/cdk-python/).

:::warning
This section is a work in progress.
:::

## Adding to Dagster

:::warning
This section is a work in progress.
We would love to see a way to integrate Airbyte plugins
into a Dagster asset (possibly via Meltano).
To track progress, see this
[GitHub issue](https://github.com/opensource-observer/oso/issues/1318).
:::
