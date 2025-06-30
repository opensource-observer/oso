MODEL (
  name oso.stg_op_atlas_application,
  description 'Staging model for OP Atlas project applications',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH source_data_raw AS (
  SELECT
    LOWER(project_id::TEXT) AS atlas_id,
    attestation_id::TEXT AS attestation_id,
    created_at::TIMESTAMP AS created_at,
    updated_at::TIMESTAMP AS updated_at,
    round_id::TEXT AS round_id,
    status::TEXT AS status
  FROM @oso_source('bigquery.op_atlas.application')
)

WITH latest_data AS (
  SELECT
    atlas_id,
    attestation_id,
    created_at,
    updated_at,
    round_id,
    status,
    ROW_NUMBER() OVER (PARTITION BY atlas_id, round_id ORDER BY updated_at DESC) AS rn
  FROM source_data_raw
)

SELECT
  atlas_id,
  attestation_id,
  created_at,
  updated_at,
  round_id,
  status
FROM latest_data
WHERE rn = 1