MODEL (
  name oso.int_sbom_from_ossd,
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
    psm.canonical_source AS package_artifact_source,
    sbom_details.artifact_namespace AS package_artifact_namespace,
    sbom_details.artifact_name AS package_artifact_name,
    sbom_details.artifact_url AS package_artifact_url,
    s.package_version,
    s.snapshot_at
  FROM oso.stg_ossd__current_sbom AS s
  JOIN oso.seed_package_source_mapping AS psm
    ON UPPER(s.package_source) = psm.package_source
  CROSS JOIN LATERAL @parse_package_artifacts(
    psm.canonical_source, s.package, psm.package_url_template
  ) AS sbom_details
),
sboms_with_ids AS (
  SELECT
    *,
    @oso_entity_id(dependent_artifact_source, dependent_artifact_namespace, dependent_artifact_name)
      AS dependent_artifact_id,
    @oso_entity_id(package_artifact_source, package_artifact_namespace, package_artifact_name)
      AS package_artifact_id
  FROM enriched_sbom_artifacts
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
FROM sboms_with_ids