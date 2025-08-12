# OSO Clickhouse Configuration Schema

the main configuration file

## Properties

- **`$schema`** **Required**
  - Type: `string`

- **`tables`**
  A list of tables available in this database

The map key is a unique table alias that defaults to defaults to "<table_schema>_<table_name>", except for tables in the "default" schema where the table name is used This is the name exposed to the engine, and may be configured by users. When the configuration is updated, the table is identified by name and schema, and changes to the alias are preserved.
  - Type: `object`

- **`queries`**
  Optionally define custom parameterized queries here Note the names must not match table names
  - Type: `object`

