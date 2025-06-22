MODEL (
  name oso.int_sbom__latest_snapshot,
  description 'The most recent snapshot of SBOMs linked to package owner GitHub repos',
  kind VIEW,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH latest_repo_snapshot AS (
  SELECT
    dependent_repo_artifact_id,
    MAX(snapshot_day) AS snapshot_day
  FROM oso.int_sbom__snapshots
  GROUP BY 1
)

SELECT DISTINCT
  sbom.snapshot_day,
  sbom.artifact_source,
  sbom.artifact_namespace,
  sbom.artifact_name,
  sbom.package_source,
  sbom.package,
  sbom.package_version,
  sbom.package_github_owner,
  sbom.package_github_repo,
  sbom.dependent_repo_artifact_id,
  sbom.dependency_repo_artifact_id,
  sbom.dependency_package_artifact_id
FROM oso.int_sbom__snapshots AS sbom
JOIN latest_repo_snapshot AS latest
  ON sbom.dependent_repo_artifact_id = latest.dependent_repo_artifact_id
  AND sbom.snapshot_day >= (latest.snapshot_day - INTERVAL '1 DAY')
