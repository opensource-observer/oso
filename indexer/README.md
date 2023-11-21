# Indexer

## Database

### Setup

Install [TimescaleDB](https://docs.timescale.com/self-hosted/latest/install/) locally for development.

_It is recommended you test any code changes against a development database first. Please do not develop against the production database._

Copy `.env.example` to `.env` and populate the `DATABASE_URL`.

### psql

For convenience, we've added a script to quickly fire up `psql` with the database configured in your `.env`

```bash
bash ./utilities/database/psql.sh
```

### Refreshing the materialized views

Sometimes a materialized view will be missing data
(for example if we insert [older historical data](https://docs.timescale.com/use-timescale/latest/continuous-aggregates/troubleshooting/#continuous-aggregate-doesnt-refresh-with-newly-inserted-historical-data))

To refresh a TimescaleDB continuous aggregate:

```sql
CALL refresh_continuous_aggregate('events_daily_to_project', '2021-05-01', '2021-06-01');
```

See [Timescale docs](https://docs.timescale.com/use-timescale/latest/continuous-aggregates/refresh-policies/#manually-refresh-a-continuous-aggregate) for more details.

Not all materialized views are supported by Timescale (for example `FirstContributionToProject`).
These views are _not_ continuously updated and must always be manually refreshed by running:

```sql
REFRESH MATERIALIZED VIEW _first_contribution_to_project;
```

See the [Postgres docs](https://www.postgresql.org/docs/current/rules-materializedviews.html) for more details.

## TypeScript / JavaScript

### Setup

Install your npm dependencies

```bash
pnpm install
```

### After pulling latest changes

After running `git pull`, make sure to run any missing migrations to make sure your local database schema matches the codebase.

```bash
pnpm migration:run
```

For more details on how to collaborate within a team with Prisma, see [here](https://www.prisma.io/docs/guides/migrate/developing-with-prisma-migrate/team-development)

### Run data fetchers

To import projects and collections from [oss-directory](https://github.com/hypercerts-org/oss-directory), run the following

```bash
pnpm start importOssDirectory
```

This will populate the database with Projects, Collections, Artifacts, and start fetching event data associated with these artifacts

TODO: fill out the rest

### Updating the database schema

All of our ORM entities are stored in `./src/db/orm-entities.ts`.
After you've made your edits, run the following to automatically generate the migration.
If you want to start with an empty migration file, use `pnpm migration:create`.

```bash
pnpm migration:generate src/db/migration/[NAME]
# OR pnpm migration:create src/db/migration/[NAME]
```

To run the migration, use `pnpm migration:run`.

## Python

### Setup

1. Set environment variables in a `.env` file. You'll need API access credentials for Alchemy, Etherscan, Github, and Supabase.

2. Install the requirements in the `requirements.txt` file.

`$ pip install -r requirements.txt`

### Adding projects

Projects must be stored in a JSON with the following fields:

- name
- description
- github_org

A database of projects can then be initialized with the following command in `src/database.py`:

`insert_projects_and_wallets_from_json("data/projects.json")`

### Fetching Github events for a project

Once the database of projects is created, you can trigger the script to gather Github events with the following command in `src/database.py`:

`insert_all_events()`

Don't forget to review constant settings for:

```
START, END = '2021-01-01T00:00:00Z', '2023-04-30T00:00:00Z'
QUERIES = ["merged PR", "issue", "created PR"]
```

Note: there is currently no detection of duplicate entries in the database, so be careful modifying these settings.

### Fetching financial transactions linked to a project's Ethereum address

The script uses Zerion to download all transaction data for a wallet address.

`$ python src/zerion_scraper.py`

It will store all of the CSV files in a local directory:

`STORAGE_DIR = "data/temp"`

Finally, these can be added to the events database through the following command in `src/database.py`:

`insert_zerion_transactions()`
