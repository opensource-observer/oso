MODEL (
  name oso.stg_ossd__current_sbom,
  description 'The most recent view of sboms from the ossd dagster source',
  dialect trino,
  kind FULL,
  audits (
    number_of_rows(threshold := 0)
  )
);

WITH ranked_sboms AS (
  SELECT
    snapshot_at,
    LOWER(artifact_namespace) AS artifact_namespace,
    LOWER(artifact_name) AS artifact_name,
    UPPER(artifact_source) AS artifact_source,
    LOWER(package) AS package,
    UPPER(package_source) AS package_source,
    LOWER(package_version) AS package_version,
    ROW_NUMBER() OVER (PARTITION BY artifact_namespace, artifact_name, artifact_source, package, package_source ORDER BY snapshot_at DESC) AS row_num
  FROM @oso_source('bigquery.ossd.sbom')
)
SELECT
  artifact_namespace,
  artifact_name,
  artifact_source,
  package,
  package_source,
  package_version,
  snapshot_at
FROM ranked_sboms
WHERE
  row_num = 1