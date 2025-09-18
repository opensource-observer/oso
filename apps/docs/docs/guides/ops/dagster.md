---
title: Dagster Playbook
sidebar_position: 2
---

# Dagster Playbook

This guide outlines common operations for working with [Dagster](https://dagster.io/) in the OSO project.

## SQLMesh Integration

Our main data models are materialized using SQLMesh. In most cases, you can trigger the `sqlmesh_all_assets` job with its default configuration to update the models.

### Restatements

If you need to run a restatement, you will need to edit the configuration of the `sqlmesh_all_assets` job. There are two ways to specify which models to restate:

- **By Entity Category**: Set `restate_by_entity_category: true` and specify a list of categories to restate. You can assign categories to models using the `entity_category=category_name` tag.
- **By Model Name**: Provide a list of model names under the `restate_models` configuration. Remember to prefix the model name with `oso.`, for example: `oso.int_events__superchain_internal_transactions`.

Dagster jobs have a default of three retry attempts. However, retries use the same configuration. If a job fails mid-process, cancel the retry and trigger a new run with the correct configuration to avoid restating models multiple times.

### Branching with Tags

We use Nessie's branching feature to ensure data consumers always have access to stable data. We maintain a `consumer` tag that points to a stable version of the data, while the `main` branch is actively updated.

Our producer, Trino, has two catalogs:

- `iceberg`: Points to the `main` branch.
- `iceberg_consumer`: Points to the `consumer` tag.

After a successful run of the `sqlmesh_all_assets` job and data verification, run the `nessie_consumer_tag_job` to update the `consumer` tag to the latest `main` commit. You can also specify a particular hash in the `to_hash` configuration to move the tag to a specific commit.

## Asset Development Workflow

When creating new Dagster assets, it's important to also write a seed file before integrating it into SQLMesh.

The workflow is as follows:

1.  **Write the Asset**:
    - Follow the cursor rules for creating new assets.
    - Keep column names consistent with the original source.
    - Perform minimal normalization and unnesting.

2.  **Run Dagster Locally**:
    - Confirm that you can materialize the source correctly.

3.  **Submit and Merge a PR**:
    - Submit a pull request with your changes and merge it into production.

4.  **Materialize in Production**:
    - Materialize the asset in the production Dagster environment.

5.  **Verify Data**:
    - Sample the data in BigQuery to confirm it's correct.

6.  **Create Seed File and Staging Model**:
    - Follow the cursor rules for creating seed files and staging models.
    - Use a sample of 5-10 rows of real data from BigQuery that cover multiple cases.
    - If there are date fields, set them to `datetime.now()`.
    - Test locally with SQLMesh until there are no errors.

7.  **Submit and Merge a PR**:
    - Submit a pull request with the seed file and staging model and merge it into production.
