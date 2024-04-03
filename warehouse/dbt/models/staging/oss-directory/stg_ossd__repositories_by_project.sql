{#
  Currently this is just Github.
  oss-directory needs some refactoring to support multiple repository providers
#}

SELECT
  repos.*,
  projects.id AS project_id,
  "GITHUB" AS repository_source,
  {{ oso_id("'GITHUB'", "'GIT_REPOSITORY'", "CAST(repos.id AS STRING)") }}
    AS artifact_id
FROM
  {{ ref('stg_ossd__current_projects') }} AS projects
CROSS JOIN
  UNNEST(JSON_QUERY_ARRAY(projects.github)) AS github
INNER JOIN
  {{ ref('stg_ossd__current_repositories') }} AS repos
  ON
    LOWER(CONCAT("https://github.com/", repos.owner))
    = LOWER(JSON_VALUE(github.url))
    OR LOWER(repos.url) = LOWER(JSON_VALUE(github.url))
