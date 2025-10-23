MODEL (
  name oso.int_ddo_repo_metrics,
  description "Metrics for Developer Data Program repositories",
  kind FULL,
  dialect trino,
  grain (artifact_id),
  tags (
    'entity_category=artifact'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  artifact_id,
  a.artifact_source_id,
  a.artifact_namespace,
  a.artifact_name,
  a.artifact_url,
  m.metric_model AS metric_model,
  m.display_name AS metric_display_name,
  km.amount AS metric_amount,
  km.sample_date AS metric_sample_date
FROM oso.int_ddp_repo_metadata AS a
JOIN oso.key_metrics_by_artifact_v0 AS km USING (artifact_id)
JOIN oso.metrics_v0 AS m USING (metric_id)

