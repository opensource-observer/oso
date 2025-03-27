MODEL (
  name oso.stg_op_atlas_project_organization,
  description 'Staging model for OP Atlas project-to-organization mappings',
  dialect trino,
  kind FULL
);

WITH cleaned_data AS (
  SELECT
    LOWER(project_id::VARCHAR) AS project_id,
    LOWER(organization_id::VARCHAR) AS organization_id,
    created_at::TIMESTAMP AS created_at,
    updated_at::TIMESTAMP AS updated_at
  FROM @oso_source('bigquery.op_atlas.project_organization')
  WHERE deleted_at IS NULL
),

latest_data AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY project_id, organization_id ORDER BY updated_at DESC) AS rn
  FROM cleaned_data
)

SELECT
  @oso_entity_id('OP_ATLAS', '', project_id) AS project_id,
  LOWER(project_id::VARCHAR) AS project_name,
  organization_id AS organization_id,
  created_at::TIMESTAMP AS created_at,
  updated_at::TIMESTAMP AS updated_at
FROM latest_data
WHERE rn = 1