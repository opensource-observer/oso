MODEL (
  name metrics.metrics_v0,
  kind FULL
);
WITH unioned_metric_names AS (
  SELECT DISTINCT metric
  FROM metrics.timeseries_metrics_to_artifact
  UNION ALL
  SELECT DISTINCT metric
  FROM metrics.timeseries_metrics_to_project
  UNION ALL
  SELECT DISTINCT metric
  FROM metrics.timeseries_metrics_to_collection
),
all_timeseries_metric_names AS (
  SELECT DISTINCT metric
  FROM unioned_metric_names
),
metrics_v0_no_casting AS (
  SELECT @oso_id('OSO', 'oso', metric) AS metric_id,
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
select metric_id::varchar,
  metric_source::varchar,
  metric_namespace::varchar,
  metric_name::varchar,
  display_name::varchar,
  description::varchar,
  raw_definition::varchar,
  definition_ref::varchar,
  aggregation_function::varchar
FROM metrics_v0_no_casting