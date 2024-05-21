CREATE TABLE {{ source }}_projects_by_collection AS
SELECT 
  c.name AS collection_slug,
  p.* AS project_slug
FROM {{ source }}_collections AS c
CROSS JOIN UNNEST(c.projects) AS p 