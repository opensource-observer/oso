MODEL (
  name oso.int_packages__current_maintainer_only,
  kind VIEW,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);


SELECT DISTINCT
  package_artifact_source,
  sbom_artifact_source,
  package_artifact_name,
  package_github_owner,
  package_github_repo,
  package_url
FROM oso.int_packages
WHERE is_current_owner = TRUE