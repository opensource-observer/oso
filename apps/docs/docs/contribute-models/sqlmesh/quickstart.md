---
title: "Quickstart: Contribute Your First Model"
sidebar_position: 1
---

:::info
This guide will help you set up a local development environment with SQLMesh and walk you through creating a simple "hello world" data model.
:::

## 1. Prerequisites

Before you begin, you'll need to have the following installed on your machine:

- [DuckDB](https://duckdb.org/) - A high-performance analytical database system.
- Python 3.8 or higher.
- Git (to clone the OSO repository).

## 2. Installation & Setup

### Install DuckDB

DuckDB is required for local development and testing of SQLMesh models.

**macOS/Linux (using Homebrew):**

```bash
brew install duckdb
```

**Debian/Ubuntu (using APT):**

```bash
sudo apt-get install duckdb
```

### Clone the OSO Repository

If you haven't already, clone the OSO repository and navigate into the directory:

```bash
git clone https://github.com/opensource-observer/oso.git
cd oso
```

### Set Up Environment Variables

Create a `.env` file at the root of the OSO repository by copying the example file:

```bash
cp .env.example .env
```

Ensure the following variables are set in your new `.env` file:

```
GOOGLE_PROJECT_ID=opensource-observer
SQLMESH_DUCKDB_LOCAL_PATH=/tmp/oso.duckdb
```

### Authenticate with Google Cloud

SQLMesh needs access to Google Cloud to fetch data. Authenticate using the gcloud CLI:

```bash
gcloud auth application-default login
```

### Install Dependencies

Install the required Python dependencies using `uv`:

```bash
uv sync
source .venv/bin/activate
```

## 3. Initialize Local Data

To work with SQLMesh locally, you need to download playground data into your local DuckDB instance. For this quickstart, we'll download a small, recent sample.

```bash
oso local initialize --max-results-per-query 10000 --max-days 7
```

This command downloads 7 days of time-series data and a maximum of 10,000 rows for other tables, which is sufficient for local development.

## 4. Create a "Hello World" Model

Now you're ready to create your first data model. We'll create a simple model that lists all projects from the Open Source Software Directory (OSSD).

### Create the Model File

Create a new SQL file in the `warehouse/oso_sqlmesh/models/intermediate` directory:

```bash
touch warehouse/oso_sqlmesh/models/intermediate/int_my_first_model.sql
```

### Add the SQL Code

Open the new file (`warehouse/oso_sqlmesh/models/intermediate/int_my_first_model.sql`) in your editor and add the following code:

```sql
MODEL (
  name oso.int_my_first_model,
  kind FULL,
  dialect trino,
  description "A simple model to list projects from OSSD."
);

SELECT
  project_id,
  project_name,
  display_name
FROM oso.stg_ossd__current_projects
```

This code defines a new model named `int_my_first_model` that performs a simple `SELECT` query on an existing staging model.

## 5. Test Your Model Locally

With the model created, you can now test it using SQLMesh's `plan` command. This command will build your model in a development environment without affecting production data.

```bash
oso local sqlmesh plan dev
```

SQLMesh will detect your new model, show you the changes, and ask for confirmation to apply them. Type `y` and press Enter.

## 6. Validate the Output

Once the plan is applied, you can query your new model's output directly in DuckDB.

First, open the local DuckDB database:

```bash
duckdb /tmp/oso.duckdb
```

Inside the DuckDB shell, run a query to see the data from your model. Note that SQLMesh creates models in a `oso__dev` schema for your development environment.

```sql
SELECT * FROM oso__dev.int_my_first_model LIMIT 10;
```

You should see a list of project IDs and names from the OSSD. Congratulations, you've successfully created and tested your first data model!

## Next Steps

Now that you have a working local environment, you can start exploring more complex topics:

- Learn about the fundamental principles in our [Core Data Modeling Concepts](./core-concepts.md).
- Follow our [How-To Guides](./how-to-guides/contribute-a-data-model.md) for more detailed contribution workflows.
