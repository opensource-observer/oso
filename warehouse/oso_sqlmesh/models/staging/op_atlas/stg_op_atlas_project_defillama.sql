MODEL (
  name oso.stg_op_atlas_project_defillama,
  dialect trino,
  kind FULL
);

SELECT
  @oso_id('OP_ATLAS', projects.id) AS project_id, /* Translating op-atlas project_id to OSO project_id */
  LOWER(defillama.value) AS artifact_source_id,
  'DEFILLAMA' AS artifact_source,
  NULL::VARCHAR AS artifact_namespace,
  defillama.value AS artifact_name,
  CONCAT('https://defillama.com/protocol/', defillama.value) AS artifact_url,
  'DEFILLAMA_PROTOCOL' AS artifact_type
FROM @oso_source('bigquery.op_atlas.project__defi_llama_slug') AS defillama
INNER JOIN @oso_source('bigquery.op_atlas.project') AS projects
  ON defillama._dlt_parent_id = projects._dlt_id