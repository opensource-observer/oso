---
title: Test and Validate Models
sidebar_position: 3
---

:::info
This guide covers various strategies for testing and validating your SQLMesh models to ensure they are accurate and reliable.
:::

## Local Testing with DuckDB

The primary way to test your models is against a local DuckDB instance. This is fast, efficient, and suitable for most development work.

### Run with Limited Data

You can test your models with a limited date range to speed up development. The `sqlmesh plan` command will build your model and intelligently determine any downstream models that also need to be rebuilt.

```bash
oso local sqlmesh plan dev --start '1 week' --end now
```

This is a great way to test your model without waiting for the entire pipeline to run.

### Validate Output

After running a plan, you can check the output of your models to ensure they're producing the expected results.

First, connect to your local DuckDB database:

```bash
duckdb /tmp/oso.duckdb
```

Then, query your model. Remember that development models are created in the `oso__dev` schema.

```sql
SELECT * FROM oso__dev.{your_model_name} LIMIT 10;
```

## Adding Tests and Audits

If your model is complex or critical, consider adding tests or audits to validate the output.

### SQLMesh Audits

Audits are built directly into your model's SQL file and are a great way to enforce data quality constraints. For example, you can ensure that key columns are never null.

```sql
MODEL (
  name oso.int_artifacts_by_project_in_op_atlas,
  kind FULL,
  dialect trino,
  description "Unifies all artifacts from OP Atlas...",
  audits (
    not_null(columns := (artifact_id, project_id))
  )
);
```

SQLMesh will run these audits as part of its execution plan.

### SQLMesh Tests

For more complex validation logic, you can write tests in separate YAML files. These tests allow you to define inputs and expected outputs for a given model.

## Advanced Testing with Trino

While DuckDB is recommended for most development, you can also test your models against a local Trino instance for more production-like validation. This requires more system resources but provides a more accurate representation of the production environment.

### Using Docker Compose (Recommended)

#### Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/install/)

Follow the instructions in the OSO repository to set up and run Trino with Docker Compose.

### Using Kubernetes with Kind

For advanced users who need to test with Kubernetes, you can set up a local Trino cluster using Kind.

#### Prerequisites

- [Docker](https://www.docker.com/)
- [Kind](https://kind.sigs.k8s.io/)
- Optional for debugging: [kubectl](https://kubernetes.io/docs/tasks/tools/) and [k9s](https://k9scli.io/topics/install/)

#### Setup

Initialize the local Trino cluster on Kubernetes:

```bash
oso ops cluster-setup
```

This can take approximately 10 minutes to complete.

#### Initialize Trino Data

Initialize the local Trino with a smaller dataset:

```bash
oso local initialize --local-trino -m 1000 -d 3
```

#### Running SQLMesh with Trino

To run SQLMesh with your local Trino instance, add the `--local-trino` flag:

```bash
oso local sqlmesh --local-trino plan
```

The `--local-trino` option should be passed before any other SQLMesh arguments.
