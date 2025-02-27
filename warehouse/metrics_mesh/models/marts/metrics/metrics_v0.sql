MODEL (
  name metrics.metrics_v0,
  kind FULL,
  dialect trino,
  tags (
    'export'
  )
);

@DEF(MAX_STAGE_OVERRIDE, 550);

-- TODO(jabolo): Remove Trino session logic once #3117 lands
SET SESSION query_max_stage_count = @MAX_STAGE_OVERRIDE;

WITH unioned_metric_names AS (
  SELECT *
  FROM metrics.int_metric_names_from_artifact
  UNION ALL
  SELECT *
  FROM metrics.int_metric_names_from_project
  UNION ALL
  SELECT *
  FROM metrics.int_metric_names_from_collection
  UNION ALL
  SELECT *
  FROM metrics.int_key_metric_names_from_artifact
  UNION ALL
  SELECT *
  FROM metrics.int_key_metric_names_from_project
  UNION ALL
  SELECT *
  FROM metrics.int_key_metric_names_from_collection
), all_timeseries_metric_names AS (
  SELECT DISTINCT
    metric
  FROM unioned_metric_names
), all_metrics_metadata AS (
  SELECT
    metric,
    display_name,
    description
  FROM metrics.metrics_metadata
), metrics_v0_no_casting AS (
  SELECT
    @oso_id('OSO', 'oso', t.metric) AS metric_id,
    'OSO' AS metric_source,
    'oso' AS metric_namespace,
    t.metric AS metric_name,
    COALESCE(m.display_name, t.metric) AS display_name,
    COALESCE(m.description, 'TODO') AS description,
    NULL AS raw_definition,
    'TODO' AS definition_ref,
    'UNKNOWN' AS aggregation_function
  FROM all_timeseries_metric_names t
  LEFT JOIN all_metrics_metadata m ON t.metric = m.metric
)
SELECT
  metric_id::TEXT,
  metric_source::TEXT,
  metric_namespace::TEXT,
  metric_name::TEXT,
  display_name::TEXT,
  description::TEXT,
  raw_definition::TEXT,
  definition_ref::TEXT,
  aggregation_function::TEXT
FROM metrics_v0_no_casting;

RESET SESSION query_max_stage_count;
