with sbom_artifacts as (
  select
    artifact_source,
    artifact_namespace,
    artifact_name,
    package_source,
    package,
    package_version,
    snapshot_at
  from {{ ref('stg_ossd__current_sbom') }}
  where package_source in (
    'CARGO',
    'GOLANG',
    'NPM',
    'PYPI'
  )
),

deps_dev_packages as (
  select distinct
    package_artifact_name,
    package_github_owner,
    package_github_repo,
    case
      when package_artifact_source = 'CARGO' then 'CARGO'
      when package_artifact_source = 'GO' then 'GOLANG'
      when package_artifact_source = 'NPM' then 'NPM'
      when package_artifact_source = 'PYPI' then 'PYPI'
      else 'OTHER'
    end as sbom_artifact_source
  from {{ ref('int_packages') }}
  where is_current_owner = true
)

select
  {#
    Because we use repo.id as the artifact_source_id for github, we need to lookup the artifact_id for the SBOM repo. If the artifact is not found, this will return null.
  #}
  all_repos.project_id,
  all_repos.artifact_id,
  sbom_artifacts.artifact_source,
  sbom_artifacts.artifact_namespace,
  sbom_artifacts.artifact_name,
  {#
    Because we only index packages that are found in OSSD, most of the time this will return a null package_artifact_id.
  #}
  all_packages.project_id as package_project_id,
  all_packages.artifact_id as package_artifact_id,
  sbom_artifacts.package_source as package_artifact_source,
  '' as package_artifact_namespace,
  sbom_artifacts.package as package_artifact_name,
  'GITHUB' as package_owner_source,
  sbom_artifacts.package_version as package_version,
  deps_dev_packages.package_github_owner,
  deps_dev_packages.package_github_repo,
  deps_dev_repos.artifact_id as package_github_artifact_id,
  deps_dev_repos.project_id as package_github_project_id,
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
left outer join deps_dev_packages
  on
    sbom_artifacts.package_source = deps_dev_packages.sbom_artifact_source
    and sbom_artifacts.package = deps_dev_packages.package_artifact_name
left outer join {{ ref('int_all_artifacts') }} as deps_dev_repos
  on
    deps_dev_packages.package_github_owner = deps_dev_repos.artifact_namespace
    and deps_dev_packages.package_github_repo = deps_dev_repos.artifact_name
