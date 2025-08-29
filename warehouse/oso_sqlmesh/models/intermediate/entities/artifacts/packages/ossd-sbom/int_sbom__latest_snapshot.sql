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
    dependent_artifact_id,
    MAX(snapshot_at) AS snapshot_at
  FROM oso.int_sbom_from_ossd
  GROUP BY 1
)

SELECT DISTINCT
  sbom.snapshot_at,
  sbom.dependent_artifact_id,
  sbom.dependent_artifact_source,
  sbom.dependent_artifact_namespace,
  sbom.dependent_artifact_name,
  sbom.package_artifact_id,
  sbom.package_artifact_source,
  sbom.package_artifact_namespace,
  sbom.package_artifact_name,
  sbom.package_artifact_url,
  sbom.package_version
FROM oso.int_sbom_from_ossd AS sbom
JOIN latest_repo_snapshot AS latest
  ON sbom.dependent_artifact_id = latest.dependent_artifact_id
  AND sbom.snapshot_at = latest.snapshot_at
