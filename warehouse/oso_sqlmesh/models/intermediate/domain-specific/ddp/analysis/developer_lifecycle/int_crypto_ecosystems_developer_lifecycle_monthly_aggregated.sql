MODEL (
  name oso.int_crypto_ecosystems_developer_lifecycle_monthly_aggregated,
  description 'Developer lifecycle states for Crypto Ecosystems with full/part time classification and state transitions, aggregated by month',
  dialect trino,
  kind full,
  grain (bucket_month, project_id, label),
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  tags (
    'entity_category=project'
  )
);

SELECT
  bucket_month,
  project_id,
  project_name,
  project_display_name,
  label,
  COUNT(DISTINCT git_user) AS developers_count
FROM oso.int_crypto_ecosystems_developer_lifecycle_monthly_enriched
WHERE is_bot = false
GROUP BY 1, 2, 3, 4, 5