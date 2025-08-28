MODEL (
  name oso.int_sboms_from_ossd,
  kind FULL,
  dialect trino,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH enriched_sbom_artifacts AS (
  SELECT
    s.artifact_source AS dependent_artifact_source,
    s.artifact_namespace AS dependent_artifact_namespace,
    s.artifact_name AS dependent_artifact_name,
    sbom_details.artifact_source AS package_artifact_source,
    sbom_details.artifact_namespace AS package_artifact_namespace,
    sbom_details.artifact_name AS package_artifact_name,
    sbom_details.artifact_url AS package_artifact_url,
    s.package_version,
    s.snapshot_at
  FROM oso.stg_ossd__current_sbom AS s
  LATERAL @parse_sbom_artifacts(s.package_source, s.package) AS sbom_details
),
sboms_with_ids AS (
  SELECT
    *,
    @oso_entity_id(dependent_artifact_source, dependent_artifact_namespace, dependent_artifact_name)
      AS dependent_artifact_id,
    @oso_entity_id(package_artifact_source, package_artifact_namespace, package_artifact_name)
      AS package_artifact_id
  FROM enriched_sbom_artifacts
),
ordered_sboms AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY dependent_artifact_id, package_artifact_id
      ORDER BY snapshot_at DESC
    ) AS rn
  FROM sboms_with_ids
)

SELECT
  dependent_artifact_id,
  dependent_artifact_source,
  dependent_artifact_namespace,
  dependent_artifact_name,
  package_artifact_id,
  package_artifact_source,
  package_artifact_namespace,
  package_artifact_name,
  package_artifact_url,
  package_version,
  snapshot_at
FROM ordered_sboms
WHERE rn = 1