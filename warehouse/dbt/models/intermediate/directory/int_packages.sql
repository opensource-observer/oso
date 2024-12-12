with deps_dev_packages as (
  select
    `Version` as package_version,
    upper(`System`) as package_artifact_source,
    lower(`Name`) as package_artifact_name,
    lower(split(`ProjectName`, '/')[0]) as package_github_owner,
    lower(split(`ProjectName`, '/')[1]) as package_github_repo
  from {{ ref('stg_deps_dev__packages') }}
)

select
  package_artifact_source,
  package_artifact_name,
  package_version,
  package_github_owner,
  package_github_repo,
  case
    when package_artifact_source = 'CARGO' then 'RUST'
    when package_artifact_source = 'NPM' then 'NPM'
    when package_artifact_source = 'PYPI' then 'PIP'
    when package_artifact_source = 'GO' then 'GO'
    when package_artifact_source = 'MAVEN' then 'MAVEN'
    when package_artifact_source = 'NUGET' then 'NUGET'
    else 'UNKNOWN'
  end as sbom_artifact_source
from deps_dev_packages
