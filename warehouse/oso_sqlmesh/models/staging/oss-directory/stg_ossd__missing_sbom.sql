MODEL (
  name oso.stg_ossd__missing_sbom,
  description 'The most recent view of sboms from the ossd dagster source',
  dialect trino,
  kind VIEW,
  audits (
    number_of_rows(threshold := 0)
  )
);

WITH all_repos AS (
  SELECT
    *
  FROM @oso_source('bigquery.ossd.repositories')
), all_ossd AS (
  SELECT
    *
  FROM @oso_source('bigquery.ossd.sbom')
  WHERE
    artifact_source = 'GITHUB'
)
SELECT
  owner AS artifact_namespace,
  name AS artifact_name,
  'GITHUB' AS artifact_source,
  url AS artifact_url,
  ingestion_time AS snapshot_at
FROM all_repos AS ar
LEFT JOIN all_ossd AS ao
  ON CONCAT(ao.artifact_namespace, '/', ao.artifact_name) = ar.name_with_owner
WHERE
  ao.artifact_namespace IS NULL