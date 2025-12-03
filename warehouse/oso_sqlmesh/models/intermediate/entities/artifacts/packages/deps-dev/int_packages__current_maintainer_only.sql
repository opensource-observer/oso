MODEL (
  name oso.int_packages__current_maintainer_only,
  kind FULL,
  ignored_rules (
    "nomissingaudits",
  ),
);

SELECT DISTINCT
  package_owner_artifact_id,
  package_owner_artifact_source,
  package_owner_artifact_namespace,
  package_owner_artifact_name,
  package_artifact_id,
  package_artifact_source,
  package_artifact_namespace,
  package_artifact_name,
  package_artifact_url
FROM oso.int_packages_from_deps_dev
WHERE is_current_owner = TRUE
