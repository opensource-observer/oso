MODEL (
  name oso.stg_op_atlas_application,
  description 'Staging model for OP Atlas project applications',
  dialect trino,
  kind FULL
);

SELECT
  @oso_id('OP_ATLAS', '', project_id) AS project_id, /* Translating op-atlas project_id to OSO project_id */
  project_id::VARCHAR AS project_name,
  attestation_id::VARCHAR AS attestation_id,
  created_at::TIMESTAMP AS created_at,
  updated_at::TIMESTAMP AS updated_at,
  round_id::VARCHAR AS round_id,
  status::VARCHAR AS status
FROM @oso_source('bigquery.op_atlas.application')
