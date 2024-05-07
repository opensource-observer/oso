with ranked_repos as (
  select
    project_id,
    owner,
    star_count,
    ROW_NUMBER() over (
      partition by project_id order by star_count desc
    ) as row_number,
    COUNT(distinct owner)
      over (partition by project_id)
      as github_owners_count
  from {{ ref('int_ossd__repositories_by_project') }}
),

project_owners as (
  select
    project_id,
    github_owners_count,
    LOWER(owner) as primary_github_owner
  {# TODO: is_git_organization #}
  from ranked_repos
  where row_number = 1
)

select
  projects.project_id,
  projects.project_source,
  projects.project_namespace,
  projects.project_name,
  projects.display_name,
  projects.description,
  project_owners.primary_github_owner,
  project_owners.github_owners_count,
  ARRAY_LENGTH(JSON_EXTRACT_ARRAY(projects.github))
    as github_artifact_count,
  ARRAY_LENGTH(JSON_EXTRACT_ARRAY(projects.blockchain))
    as blockchain_artifact_count,
  ARRAY_LENGTH(JSON_EXTRACT_ARRAY(projects.npm))
    as npm_artifact_count
from {{ ref('stg_ossd__current_projects') }} as projects
left join project_owners as project_owners
  on projects.project_id = project_owners.project_id
