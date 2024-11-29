with ranked_snapshots as (
  select
    artifact_source,
    package_source,
    package_version,
    snapshot_at,
    lower(artifact_namespace) as artifact_namespace,
    lower(artifact_name) as artifact_name,
    lower(package) as package,
    row_number() over (
      partition by
        artifact_source,
        artifact_namespace,
        artifact_name,
        package_source,
        package,
        package_version
      order by snapshot_at asc
    ) as row_num
  from {{ source('ossd', 'sbom') }}
),

sbom_artifacts as (
  select
    artifact_source,
    artifact_namespace,
    artifact_name,
    package_source,
    package,
    package_version,
    snapshot_at
  from ranked_snapshots
  where row_num = 1
)

select
  {#
    Because we use repo.id as the artifact_source_id for github, we need to lookup the artifact_id for the SBOM repo. If the artifact is not found, this will return null.
  #}
  all_repos.artifact_id,
  sbom_artifacts.artifact_source,
  sbom_artifacts.artifact_namespace,
  sbom_artifacts.artifact_name,
  {#
    Because we only index packages that are found in OSSD, most of the time this will return a null package_artifact_id.
  #}
  all_packages.artifact_id as package_artifact_id,
  sbom_artifacts.package_source as package_artifact_source,
  sbom_artifacts.package as package_artifact_name,
  sbom_artifacts.package_version as package_version,
  sbom_artifacts.snapshot_at
from sbom_artifacts
left outer join {{ ref('int_all_artifacts') }} as all_repos
  on
    sbom_artifacts.artifact_namespace = all_repos.artifact_namespace
    and sbom_artifacts.artifact_name = all_repos.artifact_name
left outer join {{ ref('int_all_artifacts') }} as all_packages
  on
    sbom_artifacts.package = all_packages.artifact_name
    and sbom_artifacts.package_source = all_packages.artifact_source
