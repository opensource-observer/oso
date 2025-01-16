CREATE TABLE {{ source }}_url_artifacts AS

SELECT 
  p.name as project_name,
  k.unnest.url as url_value,
  'WEBSITE' as url_type
FROM {{ source }}_projects as p 
CROSS JOIN UNNEST(p.websites) AS k

UNION ALL

SELECT 
  p.name as project_name,
  k.unnest.url as url_value,
  'GITHUB' as url_type
FROM {{ source }}_projects as p 
CROSS JOIN UNNEST(p.github) AS k

UNION ALL

SELECT 
  p.name as project_name,
  k.unnest.url as url_value,
  'NPM' as url_type
FROM {{ source }}_projects as p 
CROSS JOIN UNNEST(p.npm) AS k

UNION ALL

SELECT 
  p.name as project_name,
  k.unnest.url as url_value,
  'CRATES' as url_type
FROM {{ source }}_projects as p 
CROSS JOIN UNNEST(p.crates) AS k

UNION ALL

SELECT 
  p.name as project_name,
  k.unnest.url as url_value,
  'PYPI' as url_type
FROM {{ source }}_projects as p 
CROSS JOIN UNNEST(p.pypi) AS k

UNION ALL

SELECT 
  p.name as project_name,
  k.unnest.url as url_value,
  'GO' as url_type
FROM {{ source }}_projects as p 
CROSS JOIN UNNEST(p.go) AS k

UNION ALL

SELECT 
  p.name as project_name,
  k.unnest.url as url_value,
  'OPEN_COLLECTIVE' as url_type
FROM {{ source }}_projects as p 
CROSS JOIN UNNEST(p.open_collective) AS k

UNION ALL

SELECT 
  p.name as project_name,
  k.unnest.url as url_value,
  'DEFILLAMA' as url_type
FROM {{ source }}_projects as p 
CROSS JOIN UNNEST(p.defillama) AS k
