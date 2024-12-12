with latest_package as (
  select
    lower(`Name`) as package_artifact_name,
    lower(split(`ProjectName`, '/')[0]) as package_owner,
    lower(split(`ProjectName`, '/')[1]) as package_repo,
    upper(`System`) as package_artifact_source
  from (
    select
      lower(`Name`) as `Name`,
      lower(`ProjectName`) as `ProjectName`,
      upper(`System`) as `System`,
      row_number() over (
        partition by
          lower(`Name`),
          upper(`System`)
        order by `Version` desc
      ) as row_num
    from {{ ref('stg_deps_dev__packages') }}
  )
  where row_num = 1
)

select
  github_repos.project_id,
  github_repos.artifact_id,
  github_repos.artifact_source_id,
  github_repos.artifact_source,
  latest_package.package_owner as artifact_namespace,
  latest_package.package_repo as artifact_name,
  all_packages.artifact_id as package_artifact_id,
  latest_package.package_artifact_source as package_artifact_source,
  latest_package.package_artifact_name as package_artifact_name
from latest_package
left outer join {{ ref('int_all_artifacts') }} as github_repos
  on
    latest_package.package_owner = github_repos.artifact_namespace
    and latest_package.package_repo = github_repos.artifact_name
    and github_repos.artifact_source = 'GITHUB'
left outer join {{ ref('int_all_artifacts') }} as all_packages
  on
    latest_package.package_artifact_name = all_packages.artifact_name
    and latest_package.package_artifact_source = all_packages.artifact_source
where github_repos.project_id is not null
