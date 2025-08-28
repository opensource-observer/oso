MODEL (
  name oso.int_packages_from_deps_dev,
  kind FULL,
  dialect trino,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH enriched_packages AS (
  SELECT
    pkg_details.artifact_source AS package_artifact_source,
    pkg_details.artifact_namespace AS package_artifact_namespace,
    pkg_details.artifact_name AS package_artifact_name,
    pkg_details.artifact_url AS package_artifact_url,
    dd.version AS package_version,
    dd.project_name AS package_owner_project_name,
    dd.project_type AS package_owner_project_type,
    dd.relationship_type AS package_owner_relationship_type
  FROM oso.stg_deps_dev__packages AS dd
  CROSS JOIN LATERAL @parse_deps_dev_artifacts(dd.system, dd.name) AS pkg_details
),
packages_with_ids AS (
  SELECT
    package_artifact_source,
    package_artifact_namespace,
    package_artifact_name,
    package_artifact_url,
    package_version,
    package_owner_project_name,
    package_owner_project_type,
    package_owner_relationship_type,
    @oso_entity_id(package_artifact_source, package_artifact_namespace, package_artifact_name) AS package_artifact_id
  FROM enriched_packages
),
latest_packages_ranked AS (
  SELECT
    package_artifact_id,
    package_owner_project_name,
    -- naive semver parse: major.minor.patch
    TRY(CAST(regexp_extract(package_version,'^([0-9]+)',1) AS integer)) AS v_major,
    TRY(CAST(regexp_extract(package_version,'^[0-9]+\\.([0-9]+)',1) AS integer)) AS v_minor,
    TRY(CAST(regexp_extract(package_version,'^[0-9]+\\.[0-9]+\\.([0-9]+)',1) AS integer)) AS v_patch,
    row_number() OVER (
      PARTITION BY package_artifact_id
      ORDER BY v_major DESC NULLS LAST, v_minor DESC NULLS LAST, v_patch DESC NULLS LAST, package_version DESC
    ) AS rn
  FROM packages_with_ids
),
latest_packages AS (
  SELECT package_artifact_id, package_owner_project_name
  FROM latest_packages_ranked
  WHERE rn=1
),
latest_owner AS (
  SELECT
    p.*,
    (p.package_owner_project_name=lp.package_owner_project_name)
      AS is_current_owner
  FROM packages_with_ids p
  JOIN latest_packages lp ON p.package_artifact_id=lp.package_artifact_id
),
packages_and_projects AS (
  SELECT
    package_artifact_id,
    package_artifact_source,
    package_artifact_namespace,
    package_artifact_name,
    package_artifact_url,
    package_version,
    package_owner_project_name,
    -- owner: first segment; repo: everything after first '/'
    regexp_extract(package_owner_project_name,'^([^/]+)',1) AS package_owner_artifact_namespace,
    regexp_extract(package_owner_project_name,'^[^/]+/(.+)$',1) AS package_owner_artifact_name,
    package_owner_project_type AS package_owner_artifact_source,
    package_owner_relationship_type,
    is_current_owner
  FROM latest_owner
)

SELECT
  @oso_entity_id(package_owner_artifact_source, package_owner_artifact_namespace, package_owner_artifact_name) AS package_owner_artifact_id,
  package_owner_artifact_source,
  package_owner_artifact_namespace,
  package_owner_artifact_name,
  package_artifact_id,
  package_artifact_source,
  package_artifact_namespace,
  package_artifact_name,
  package_artifact_url,
  package_version,
  package_owner_relationship_type,
  is_current_owner
FROM packages_and_projects