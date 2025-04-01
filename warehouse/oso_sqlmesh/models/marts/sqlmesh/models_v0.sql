MODEL (
  name oso.models_v0,
  kind FULL,
  tags (
    'export',
    'model_type=full',
    'model_category=sqlmesh',
    'model_stage=mart'
  )
);

WITH all_timeseries_metrics_by_project AS (
  SELECT
    @oso_id('OSO', 'sqlmesh', model_name) AS model_id,
    model_name,
    rendered_sql,
    rendered_at,
  FROM oso.stg_sqlmesh__rendered_models
)
SELECT
    model_id::TEXT,
    model_name::TEXT,
    rendered_sql::TEXT,
    rendered_at::TIMESTAMP
FROM all_timeseries_metrics_by_project
