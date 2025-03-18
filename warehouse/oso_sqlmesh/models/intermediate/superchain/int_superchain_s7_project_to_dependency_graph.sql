MODEL (
  name oso.int_superchain_s7_project_to_dependency_graph,
  description "Maps relationships between onchain builder projects and their devtooling dependencies",
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column sample_date,
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by DAY("sample_date"),
  grain (
    sample_date,
    onchain_builder_project_id,
    devtooling_project_id,
    dependent_artifact_id,
    dependency_artifact_id
  ),
  enabled false
);

WITH onchain_builder_projects AS (
  SELECT
    project_id AS onchain_builder_project_id,
    is_eligible,
    sample_date::TIMESTAMP AS sample_date
  FROM oso.int_superchain_s7_onchain_builder_eligibility
), devtooling_projects AS (
  SELECT
    project_id AS devtooling_project_id,
    repo_artifact_id,
    is_eligible,
    sample_date::TIMESTAMP AS sample_date
  FROM oso.int_superchain_s7_devtooling_repo_eligibility
)
SELECT
  onchain_builder_projects.sample_date,
  onchain_builder_projects.onchain_builder_project_id,
  devtooling_projects.devtooling_project_id,
  dependencies.dependent_artifact_id,
  dependencies.dependency_artifact_id,
  dependencies.dependency_name,
  dependencies.dependency_source
FROM oso.int_code_dependencies AS dependencies
INNER JOIN oso.int_repositories_enriched AS dependents
  ON dependencies.dependent_artifact_id = dependents.artifact_id
INNER JOIN onchain_builder_projects
  ON dependents.project_id = onchain_builder_projects.onchain_builder_project_id
INNER JOIN devtooling_projects
  ON dependencies.dependency_artifact_id = devtooling_projects.repo_artifact_id
  AND onchain_builder_projects.sample_date = devtooling_projects.sample_date
WHERE
  onchain_builder_projects.onchain_builder_project_id <> devtooling_projects.devtooling_project_id
  AND onchain_builder_projects.is_eligible
  AND devtooling_projects.is_eligible