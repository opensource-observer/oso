MODEL (
  name oso.int_optimism_grants,
  description 'Optimism grants',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  ),
  tags (
    'entity_category=project'
  )
);

WITH grants AS (
  SELECT
    f.funding_date,
    p.project_name,
    p.display_name,
    p.project_id,
    f.grant_pool_name,
    CASE
      WHEN LOWER(f.grant_pool_name) LIKE 'retro%' THEN 'RETRO_FUNDING'
      ELSE 'GRANTS_COUNCIL'
    END AS grant_mechanism,
    f.amount AS amount_usd,
    JSON_EXTRACT_SCALAR(f.metadata, '$.token_amount') AS amount_op,
    JSON_EXTRACT_SCALAR(f.metadata, '$.application_name') AS application_name,
    JSON_EXTRACT_SCALAR(f.metadata, '$.initial_delivery_date')
      AS initial_delivery_date
  FROM oso.stg_ossd__current_funding AS f
  LEFT JOIN oso.projects_v1 AS p
    ON f.to_project_name = p.project_name
    AND p.project_source = 'OSS_DIRECTORY'
    AND p.project_namespace = 'oso'
  WHERE f.from_funder_name = 'optimism'
)

SELECT
  funding_date::DATE AS funding_date,
  application_name::VARCHAR AS application_name,
  grant_pool_name::VARCHAR AS grant_round,
  grant_mechanism::VARCHAR AS grant_mechanism,
  amount_op::DOUBLE AS amount_op,
  initial_delivery_date::DATE AS initial_delivery_date,
  amount_usd::DOUBLE AS amount_usd,
  project_name::VARCHAR AS oso_project_name,
  display_name::VARCHAR AS oso_project_display_name,
  project_id::VARCHAR AS oso_project_id
FROM grants