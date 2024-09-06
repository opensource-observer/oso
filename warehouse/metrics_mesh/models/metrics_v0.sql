MODEL (
  name metrics.metrics_v0,
  kind FULL,
  dialect "clickhouse"
);
WITH all_timeseries_metric_names AS (
  SELECT DISTINCT 
    metric
  FROM metrics.timeseries_metrics_by_artifact_over_30_days
),
metrics_v0_no_casting AS (
  SELECT 
    @oso_id('OSO', 'oso', metric) AS metric_id,
    'OSO' AS metric_source,
    'oso' AS metric_namespace,
    metric AS metric_name,
    metric AS display_name,
    'TODO' AS description,
    NULL AS raw_definition,
    'TODO' AS definition_ref,
    'UNKNOWN' AS aggregation_function
  FROM all_timeseries_metric_names
)
select 
  metric_id::String,
  metric_source::String,
  metric_name::String,
  display_name::String,
  description::Nullable(String),
  raw_definition::Nullable(String),
  definition_ref::Nullable(String),
  aggregation_function::Nullable(String)
FROM metrics_v0_no_casting