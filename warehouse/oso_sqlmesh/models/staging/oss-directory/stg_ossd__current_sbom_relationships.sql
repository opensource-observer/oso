MODEL (
  name oso.stg_ossd__current_sbom_relationships,
  description 'The most recent view of sbom relationships from the ossd dagster source',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH ranked_sboms AS (
  SELECT
    snapshot_at,
    LOWER(artifact_namespace) AS artifact_namespace,
    LOWER(artifact_name) AS artifact_name,
    UPPER(artifact_source) AS artifact_source,
    UPPER(relationship_type) AS relationship_type,
    LOWER(spdx_element_id) AS spdx_element_id,
    LOWER(related_spdx_element) AS related_spdx_element,
    ROW_NUMBER() OVER (
      PARTITION BY artifact_namespace, artifact_name, artifact_source, spdx_element_id, related_spdx_element 
      ORDER BY snapshot_at DESC
    ) AS row_num
  FROM @oso_source('bigquery.ossd.sbom_relationships')
)
SELECT
  artifact_namespace,
  artifact_name,
  artifact_source,
  relationship_type,
  spdx_element_id,
  related_spdx_element,
  snapshot_at,
FROM ranked_sboms
WHERE
  row_num = 1