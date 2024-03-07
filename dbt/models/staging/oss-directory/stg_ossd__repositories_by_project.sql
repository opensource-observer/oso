SELECT
  projects.id AS project_id,
  {# 
    Currently this is just Github. 
    oss-directory needs some refactoring to support multiple repository providers 
  #}
  "GITHUB" AS repository_source,
  repos.*
FROM
  {{ ref('stg_ossd__current_projects')}} AS projects
CROSS JOIN
  UNNEST(JSON_QUERY_ARRAY(projects.github)) AS github
INNER JOIN
  {{ ref('stg_ossd__current_repositories') }} AS repos
ON
  LOWER(CONCAT("https://github.com/", repos.owner)) = LOWER(JSON_VALUE(github.url))
  OR LOWER(repos.url) = LOWER(JSON_VALUE(github.url))