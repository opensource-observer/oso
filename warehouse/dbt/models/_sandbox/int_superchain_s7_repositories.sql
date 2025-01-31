{{
  config(
    materialized='table'
  )
}}

with releases as (
  select
    to_artifact_id as repo_artifact_id,
    max(`time`) as last_release_published
  from {{ ref('int_events__github') }}
  where event_type = 'RELEASE_PUBLISHED'
  group by to_artifact_id
),

packages as (
  select
    package_github_artifact_id,
    max(coalesce(package_artifact_source = 'NPM', false)) as has_npm_package,
    max(coalesce(package_artifact_source = 'CARGO', false)) as has_rust_package,
    count(distinct artifact_id) as num_dependent_repos_in_oso
  from {{ ref('int_sbom_artifacts') }}
  where package_github_project_id != project_id
  group by package_github_artifact_id
)

select distinct
  repos.project_id,
  repos.artifact_id as repo_artifact_id,
  repos.artifact_source_id as repo_github_node_id,
  repos.artifact_namespace as repo_owner,
  repos.artifact_name as repo_name,
  repos.artifact_url as repo_url,
  repos.is_fork,
  repos.star_count,
  repos.fork_count,
  repos.license_name,
  repos.license_spdx_id,
  repos.`language`,
  repos.created_at,
  repos.updated_at,
  releases.last_release_published,
  coalesce(packages.has_npm_package, false) as has_npm_package,
  coalesce(packages.has_rust_package, false) as has_rust_package,
  coalesce(packages.num_dependent_repos_in_oso, 0) as num_dependent_repos_in_oso
from {{ ref('int_repositories') }} as repos
left join releases
  on repos.artifact_id = releases.repo_artifact_id
left join packages
  on repos.artifact_id = packages.package_github_artifact_id
inner join {{ ref('projects_v1') }} as projects
  on repos.project_id = projects.project_id
where projects.project_namespace = 'oso'
