CREATE TABLE {{ source }}_code_artifacts AS
SELECT 
  p.slug as project_slug,
  gh.github.url as code_url,
  'GITHUB' as code_host
FROM {{ source }}_projects as p 
CROSS JOIN UNNEST(p.github) AS gh 