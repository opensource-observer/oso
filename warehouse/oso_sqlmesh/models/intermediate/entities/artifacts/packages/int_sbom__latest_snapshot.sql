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
),

latest_sboms AS (
  SELECT *
  FROM oso.int_sbom__snapshots AS sbom
  JOIN latest_repo_snapshot AS latest
    ON sbom.dependent_repo_artifact_id = latest.dependent_repo_artifact_id
    AND sbom.snapshot_day >= (latest.snapshot_day - INTERVAL '1 DAY')
)

SELECT DISTINCT
  snapshot_day,
  artifact_source,
  artifact_namespace,
  artifact_name,
  package_source,
  package,
  package_version,
  package_github_owner,
  package_github_repo,
  dependent_repo_artifact_id,
  dependency_repo_artifact_id,
  dependency_package_artifact_id
FROM latest_sboms
