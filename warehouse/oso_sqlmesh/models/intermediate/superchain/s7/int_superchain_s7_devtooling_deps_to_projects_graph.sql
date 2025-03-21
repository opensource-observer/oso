MODEL (
  name oso.int_superchain_s7_devtooling_deps_to_projects_graph,
  description 'Maps relationships between onchain builder projects and their dependencies',
  dialect trino,
  kind full,
  grain (onchain_builder_project_id, devtooling_project_id),
);

@DEF(active_onchain_builder_date_threshold, DATE('2024-01-01'));

SELECT DISTINCT
  onchain_builders.project_id AS onchain_builder_project_id,
  devtools.project_id AS devtooling_project_id,
  code_deps.dependency_source
FROM oso.int_code_dependencies AS code_deps
JOIN oso.int_repositories_enriched AS onchain_builders
  ON code_deps.dependent_artifact_id = onchain_builders.artifact_id
JOIN oso.int_superchain_s7_devtooling_repositories AS devtools
  ON code_deps.dependency_artifact_id = devtools.repo_artifact_id
WHERE
  onchain_builders.project_id != devtools.project_id
  AND onchain_builders.updated_at >= @active_onchain_builder_date_threshold
  AND onchain_builders.project_id IN (
    SELECT project_id
    FROM oso.int_superchain_s7_devtooling_onchain_builder_nodes
  )
  