MODEL (
  name oso.int_raw_artifacts,
  description "Standardized schema for artifacts from all sources",
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

/*
  This model consolidates artifacts from all sources into a standardized schema.
  It relies on source-specific interface models that handle the transformation
  from source-specific schemas to this standard schema.
  
  Benefits:
  - Single source of truth for all artifacts
  - Consistent schema regardless of source
  - Easier to add new sources
  - Clearer separation between source-specific logic and common processing
*/

WITH ossd_artifacts AS (
  SELECT
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type,
    project_id,
    'OSSD' AS data_source,
    last_updated_at
  FROM oso.int_ossd_interface
), 

op_atlas_artifacts AS (
  SELECT
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type,
    project_id,
    'OP_ATLAS' AS data_source,
    last_updated_at
  FROM oso.int_op_atlas_interface
),

blockchain_artifacts AS (
  SELECT
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type,
    project_id,
    'BLOCKCHAIN' AS data_source,
    last_updated_at
  FROM oso.int_blockchain_interface
),

all_artifacts AS (
  SELECT * FROM ossd_artifacts
  UNION ALL
  SELECT * FROM op_atlas_artifacts
  UNION ALL
  SELECT * FROM blockchain_artifacts
),

-- Handle potential duplicates across sources with a priority-based approach
deduplicated_artifacts AS (
  SELECT
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type,
    project_id,
    data_source,
    last_updated_at,
    -- Create a priority field for deduplication
    ROW_NUMBER() OVER (
      PARTITION BY artifact_id
      ORDER BY 
        -- Prioritize sources (can be adjusted based on data quality)
        CASE 
          WHEN data_source = 'OP_ATLAS' THEN 1
          WHEN data_source = 'OSSD' THEN 2
          WHEN data_source = 'BLOCKCHAIN' THEN 3
          ELSE 99
        END,
        -- For same source, take the most recently updated
        last_updated_at DESC
    ) AS priority
  FROM all_artifacts
)

-- Final output with standardized schema
SELECT
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  artifact_type,
  project_id,
  data_source,
  last_updated_at
FROM deduplicated_artifacts
WHERE priority = 1  -- Take only the highest priority record for each artifact_id
