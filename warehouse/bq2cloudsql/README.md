# bq2cloudsql

This utility script copies the final mart models from the end of
the dbt pipeline into a Google CloudSQL postgres database for
serving the API / frontend.

The general strategy is to dump the models into CSV files
on GCS, then import them into the Postgres database
into temporary tables. When the copy is done, we drop the old tables
and rename the fresh import.

Note: Because we only maintain a single database, this operation can
severely load the production server during copies.

## Setup

Copy `.env.example` to `.env` in the root of the monorepo.
Populate the values there.

Then from the monorepo root, run install Python dependencies

```bash
uv sync
```

## Running

Run the copy with

```bash
uv run bq2cloudsql
```

Note: this command is defined in the root `pyproject.toml`

## Development

For now, we've been developing / testing this on the production servers.
In the future, we should create staging and development databases for this.

You can copy only select tables by slicing `table_sync_configs` in `./script.py`.
