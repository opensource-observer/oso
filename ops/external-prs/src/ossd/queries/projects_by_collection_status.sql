CREATE TABLE projects_by_collection_status AS
WITH all_projects_by_collection_status AS (
  SELECT 
    CASE 
      WHEN main.collection_slug IS NOT NULL THEN main.collection_slug
      ELSE pr.collection_slug
    END AS collection_slug,
    CASE 
      WHEN main.collection_slug IS NOT NULL THEN main.project_slug
      ELSE pr.project_slug
    END AS project_slug,
    CASE
      WHEN main.collection_slug IS NOT NULL AND pr.collection_slug IS NOT NULL THEN 'EXISTING'
      WHEN main.collection_slug IS NOT NULL AND pr.collection_slug IS NULL THEN 'REMOVED'
      ELSE 'ADDED'
    END AS status
  FROM main_projects_by_collection AS main
  FULL OUTER JOIN pr_projects_by_collection AS pr
    ON main.collection_slug = pr.collection_slug AND main.project_slug = pr.project_slug
)
SELECT 
  apbcs.collection_slug,
  apbcs.project_slug,
  apbcs.status AS relation_status,
  ps.status AS project_status
FROM all_projects_by_collection_status as apbcs
INNER JOIN project_status AS ps
  ON ps.project_slug = apbcs.project_slug
