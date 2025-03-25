MODEL (
  name oso.stg_deps_dev__packages,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column snapshot_at,
    batch_size 90,
    batch_concurrency 3,
    lookback 7
  ),
  start DATE('2025-01-01'),
  partitioned_by (DAY(snapshot_at), package_artifact_source),
);

-- SELECT
--   "SnapshotAt"::TIMESTAMP as snapshot_at,
--   UPPER("System")::VARCHAR as package_artifact_source,
--   LOWER("ProjectName")::VARCHAR as package_github_owner_and_repo,
--   LOWER("Name")::VARCHAR as package_name,
--   LOWER("Version")::VARCHAR as package_version
-- FROM @oso_source('bigquery.deps_dev_v1.package_version_to_project')
-- WHERE "ProjectName" is not null
--   AND "ProjectType" = 'GITHUB'
--   AND "RelationType" = 'SOURCE_REPO_TYPE'


SELECT
  DATE('2025-03-24') as snapshot_at,
  package_artifact_source,
  package_github_owner_and_repo,
  package_name,
  package_version
FROM VALUES
  ('NPM', 'opensource-observer/oso', '@example/oso', '0.0.16')
  AS t(package_artifact_source, package_github_owner_and_repo, package_name, package_version)