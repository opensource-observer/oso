{#
  Currently this is just Github.
  oss-directory needs some refactoring to support multiple repository providers
#}
with all_repos_by_project as (
  select
    repos.*,
    projects.project_id,
    "GITHUB" as repository_source
  from
    {{ ref('stg_ossd__current_projects') }} as projects
  cross join
    UNNEST(JSON_QUERY_ARRAY(projects.github)) as github
  inner join
    {{ ref('stg_ossd__current_repositories') }} as repos
    on
      LOWER(CONCAT("https://github.com/", repos.owner))
      = LOWER(JSON_VALUE(github.url))
      or LOWER(repos.url) = LOWER(JSON_VALUE(github.url))
)

select
  all_repos.*,
  {{ 
    oso_id(
      "repository_source",
      "all_repos.owner",
      "CAST(all_repos.id AS STRING)"
    ) 
  }} as artifact_id
from all_repos_by_project as all_repos
