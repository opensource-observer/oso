with latest_package as (
  select distinct
    package_artifact_source,
    package_artifact_name,
    package_github_owner,
    package_github_repo
  from {{ ref('int_packages') }}
  where is_current_owner = true
)

select
  github_repos.project_id,
  github_repos.artifact_id,
  github_repos.artifact_source_id,
  github_repos.artifact_source,
  latest_package.package_github_owner as artifact_namespace,
  latest_package.package_github_repo as artifact_name,
  all_packages.artifact_id as package_artifact_id,
  latest_package.package_artifact_source as package_artifact_source,
  latest_package.package_artifact_name as package_artifact_name
from latest_package
left outer join {{ ref('int_all_artifacts') }} as github_repos
  on
    latest_package.package_github_owner = github_repos.artifact_namespace
    and latest_package.package_github_repo = github_repos.artifact_name
    and github_repos.artifact_source = 'GITHUB'
left outer join {{ ref('int_all_artifacts') }} as all_packages
  on
    latest_package.package_artifact_name = all_packages.artifact_name
    and latest_package.package_artifact_source = all_packages.artifact_source
where github_repos.project_id is not null
