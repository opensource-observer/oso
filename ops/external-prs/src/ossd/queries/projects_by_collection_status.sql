CREATE TABLE projects_by_collection_status AS
WITH all_projects_by_collection_status AS (
  SELECT 
    CASE 
      WHEN main.collection_name IS NOT NULL THEN main.collection_name
      ELSE pr.collection_name
    END AS collection_name,
    CASE 
      WHEN main.collection_name IS NOT NULL THEN main.project_name
      ELSE pr.project_name
    END AS project_name,
    CASE
      WHEN main.collection_name IS NOT NULL AND pr.collection_name IS NOT NULL THEN 'EXISTING'
      WHEN main.collection_name IS NOT NULL AND pr.collection_name IS NULL THEN 'REMOVED'
      ELSE 'ADDED'
    END AS status
  FROM main_projects_by_collection AS main
  FULL OUTER JOIN pr_projects_by_collection AS pr
    ON main.collection_name = pr.collection_name AND main.project_name = pr.project_name
)
SELECT 
  apbcs.collection_name,
  apbcs.project_name,
  apbcs.status AS relation_status,
  ps.status AS project_status
FROM all_projects_by_collection_status as apbcs
INNER JOIN project_status AS ps
  ON ps.project_name = apbcs.project_name
