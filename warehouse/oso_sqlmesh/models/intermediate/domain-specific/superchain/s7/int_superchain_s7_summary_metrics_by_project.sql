MODEL (
  name oso.int_superchain_s7_summary_metrics_by_project,
  description "S7 Retro Funding summary metrics by project",
  dialect trino,
  kind full,
  grain (project_id, sample_date, metric_name),
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  enabled false,
);


@DEF(default_sample_date, DATE '2025-07-01');

WITH onchain_builder_eligibility AS (
  SELECT DISTINCT
    project_id,
    sample_date,
    'S7_ONCHAIN_BUILDERS_gas_fees_over_180_days' AS metric_name,
    gas_fees::DOUBLE AS amount,
    'ETH' AS unit
  FROM oso.int_superchain_s7_onchain_builder_eligibility
  UNION ALL
  SELECT DISTINCT
    project_id,
    sample_date,
    'S7_ONCHAIN_BUILDERS_transactions_over_180_days' AS metric_name,
    transaction_count::DOUBLE AS amount,
    'unique transaction hashes' AS unit
  FROM oso.int_superchain_s7_onchain_builder_eligibility
  UNION ALL
  SELECT DISTINCT
    project_id,
    sample_date,
    'S7_ONCHAIN_BUILDERS_active_days_over_180_days' AS metric_name,
    active_days::DOUBLE AS amount,
    'days' AS unit
  FROM oso.int_superchain_s7_onchain_builder_eligibility
  UNION ALL
  SELECT DISTINCT
    project_id,
    sample_date,
    'S7_ONCHAIN_BUILDERS_is_eligible' AS metric_name,
    meets_all_criteria::DOUBLE AS amount,
    'boolean' AS unit
  FROM oso.int_superchain_s7_onchain_builder_eligibility
),

onchain_builder_metrics AS (
  SELECT
    project_id,
    sample_date,
    CONCAT('S7_ONCHAIN_BUILDERS_', metric_name) AS metric_name,
    SUM(amount)::DOUBLE AS amount,
    '' AS unit
  FROM oso.int_superchain_s7_onchain_metrics_by_project
  GROUP BY 1, 2, 3
),

devtooling_metrics AS (
  SELECT DISTINCT
    project_id,
    @default_sample_date AS sample_date,
    'S7_DEVTOOLING_is_eligible' AS metric_name,
    is_eligible::DOUBLE AS amount,
    'boolean' AS unit
  FROM oso.int_superchain_s7_devtooling_metrics_by_project
  UNION ALL
  SELECT DISTINCT
    project_id,
    @default_sample_date AS sample_date,
    'S7_DEVTOOLING_incremental_star_count' AS metric_name,
    star_count::DOUBLE AS amount,
    'stars' AS unit
  FROM oso.int_superchain_s7_devtooling_metrics_by_project
  UNION ALL
  SELECT DISTINCT
    project_id,
    @default_sample_date AS sample_date,
    'S7_DEVTOOLING_incremental_fork_count' AS metric_name,
    fork_count::DOUBLE AS amount,
    'forks' AS unit
  FROM oso.int_superchain_s7_devtooling_metrics_by_project
  UNION ALL
  SELECT DISTINCT
    project_id,
    @default_sample_date AS sample_date,
    'S7_DEVTOOLING_num_packages_in_deps_dev' AS metric_name,
    num_packages_in_deps_dev::DOUBLE AS amount,
    'packages' AS unit
  FROM oso.int_superchain_s7_devtooling_metrics_by_project
  UNION ALL
  SELECT DISTINCT
    project_id,
    @default_sample_date AS sample_date,
    'S7_DEVTOOLING_package_connection_count' AS metric_name,
    package_connection_count::DOUBLE AS amount,
    'connections to onchain builder projects' AS unit
  FROM oso.int_superchain_s7_devtooling_metrics_by_project
  UNION ALL
  SELECT DISTINCT
    project_id,
    @default_sample_date AS sample_date,
    'S7_DEVTOOLING_developer_connection_count' AS metric_name,
    developer_connection_count::DOUBLE AS amount,
    'connections to trusted onchain developers' AS unit
  FROM oso.int_superchain_s7_devtooling_metrics_by_project
  UNION ALL
  SELECT DISTINCT
    project_id,
    @default_sample_date AS sample_date,
    'S7_DEVTOOLING_onchain_builder_oso_project_count' AS metric_name,
    ARRAY_LENGTH(onchain_builder_oso_project_ids)::DOUBLE AS amount,
    'onchain builder projects' AS unit
  FROM oso.int_superchain_s7_devtooling_metrics_by_project
  UNION ALL
  SELECT DISTINCT
    project_id,
    @default_sample_date AS sample_date,
    'S7_DEVTOOLING_onchain_builder_op_atlas_count' AS metric_name,
    ARRAY_LENGTH(onchain_builder_op_atlas_ids)::DOUBLE AS amount,
    'onchain builder projects' AS unit
  FROM oso.int_superchain_s7_devtooling_metrics_by_project
),

all_metrics AS (
  SELECT * FROM onchain_builder_eligibility
  UNION ALL
  SELECT * FROM onchain_builder_metrics
  UNION ALL
  SELECT * FROM devtooling_metrics
)

SELECT
  project_id,
  sample_date,
  metric_name,
  amount,
  unit
FROM all_metrics