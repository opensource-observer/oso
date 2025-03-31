MODEL (
  name oso.stg_sqlmesh__rendered_models,
  description 'Formatted SQLMesh source SQL for all models',
  dialect trino,
  kind FULL
);

SELECT
  models.model_name,
  models.rendered_sql,
  models.rendered_at,
FROM @oso_source('bigquery.sqlmesh.rendered_models') AS models
