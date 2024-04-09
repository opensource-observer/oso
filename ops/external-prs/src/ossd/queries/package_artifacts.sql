CREATE TABLE {{ source }}_package_artifacts AS
SELECT 
  p.slug as project_slug,
  npm.npm.url as package_url,
  'NPM' as package_host
FROM {{ source }}_projects as p 
CROSS JOIN UNNEST(p.npm) AS npm