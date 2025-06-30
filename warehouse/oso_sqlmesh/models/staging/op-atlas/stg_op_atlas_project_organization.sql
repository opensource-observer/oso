MODEL (
  name oso.stg_op_atlas_project_organization,
  description 'Staging model for OP Atlas project-to-organization mappings',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH cleaned_data AS (
  SELECT
    LOWER(project_id::TEXT) AS atlas_id,
    LOWER(organization_id::TEXT) AS organization_id,
    created_at::TIMESTAMP AS created_at,
    updated_at::TIMESTAMP AS updated_at
  FROM @oso_source('bigquery.op_atlas.project_organization')
  WHERE deleted_at IS NULL
),

latest_data AS (
  SELECT
    atlas_id,
    organization_id,
    created_at,
    updated_at,
    ROW_NUMBER() OVER (PARTITION BY atlas_id, organization_id ORDER BY updated_at DESC) AS rn
  FROM cleaned_data
)

SELECT
  atlas_id,
  organization_id,
  created_at,
  updated_at
FROM latest_data
WHERE rn = 1