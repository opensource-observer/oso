{#
  Currently this is just Github.
  oss-directory needs some refactoring to support multiple repository providers
#}

select
  repos.*,
  projects.project_id,
  "GITHUB" as repository_source,
  {{ oso_id("'GITHUB'", "'GIT_REPOSITORY'", "CAST(repos.id AS STRING)") }}
    as artifact_id
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
