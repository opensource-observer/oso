MODEL (
  name oso.int_superchain_s7_relational_metrics_by_project,
  description "S7 Retro Funding relational metrics by project",
  dialect trino,
  kind full,
  grain (project_id, sample_date, metric_name),
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);


WITH relational_metrics AS (
  SELECT
    project_id,
    current_date() AS sample_date,
    'S7_DEVTOOLING_onchain_builder_oso_project_ids' AS metric_name,
    onchain_builder_oso_project_ids AS related_entities,
    'list of OSO project ids' AS unit
  FROM oso.int_superchain_s7_devtooling_metrics_by_project
  UNION ALL
  SELECT
    project_id,
    current_date() AS sample_date,
    'S7_DEVTOOLING_onchain_builder_op_atlas_ids' AS metric_name,
    onchain_builder_op_atlas_ids AS related_entities,
    'list of OP Atlas project ids' AS unit
  FROM oso.int_superchain_s7_devtooling_metrics_by_project
  UNION ALL
  SELECT
    project_id,
    current_date() AS sample_date,
    'S7_DEVTOOLING_trusted_developer_usernames' AS metric_name,
    trusted_developer_usernames AS related_entities,
    'list of GitHub usernames' AS unit
  FROM oso.int_superchain_s7_devtooling_metrics_by_project
)

SELECT
  project_id,
  sample_date,
  metric_name,
  related_entities,
  unit
FROM relational_metrics
