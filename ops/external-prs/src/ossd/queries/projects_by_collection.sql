CREATE TABLE {{ source }}_projects_by_collection AS
SELECT 
  c.name AS collection_name,
  p.* AS project_name
FROM {{ source }}_collections AS c
CROSS JOIN UNNEST(c.projects) AS p 