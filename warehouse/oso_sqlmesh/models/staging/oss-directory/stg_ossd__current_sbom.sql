MODEL (
  name oso.stg_ossd__current_sbom,
  description 'SBOM snapshots from the OSSD dagster source',
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column snapshot_at,
    batch_size 180,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
  ),
  cron '@weekly',
  partitioned_by (DAY("snapshot_at"), "package_source"),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  ignored_rules (
    "incrementalmustdefinenogapsaudit",
  ),
  tags (
    "ossd",
    "incremental",
  ),
);


SELECT DISTINCT
  snapshot_at::TIMESTAMP AS snapshot_at,
  LOWER(artifact_namespace) AS artifact_namespace,
  LOWER(artifact_name) AS artifact_name,
  UPPER(artifact_source) AS artifact_source,
  LOWER(package) AS package,
  UPPER(package_source) AS package_source,
  LOWER(package_version) AS package_version
FROM @oso_source('bigquery.ossd.sbom')
WHERE snapshot_at BETWEEN @start_dt AND @end_dt