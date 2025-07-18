MODEL (
  name oso.model_activity_daily_v0,
  kind FULL,
  tags (
    'export',
    'model_type=full',
    'model_category=sqlmesh',
    'model_stage=mart'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  description 'Each row represents daily model activity counts for models that match specific naming patterns. This data can be used to monitor SQLMesh pipeline health, identify peak processing times, and analyze model usage patterns. Business questions that can be answered include: Which models are most frequently executed? What are the daily activity patterns in the SQLMesh pipeline? How has model execution volume changed over time?',
  column_descriptions (
    rendered_date = 'The date when the models were rendered/executed.',
    model_name = 'The name of the model that was rendered/executed.',
    daily_count = 'The count of times this model was rendered/executed on this date.'
  )
);

WITH filtered_models AS (
  SELECT 
    models.model_name,
    DATE(models.rendered_at) AS rendered_date
  FROM oso.models_v0 AS models
  WHERE 
    @regexp_like(models.model_name, '^int_events__[^d].*') OR
    @regexp_like(models.model_name, '^int_events_daily__.*') OR
    models.model_name = 'stg_github__events' OR
    @regexp_like(models.model_name, '^stg_superchain__.*') OR
    @regexp_like(models.model_name, '^stg_worldchain__.*')
)

SELECT
  rendered_date::DATE,
  model_name::TEXT,
  COUNT(*)::INT AS daily_count
FROM filtered_models
GROUP BY rendered_date, model_name
