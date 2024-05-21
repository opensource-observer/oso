-- Get the status of a project based on it's slug.
-- Is it an entirely new project?
-- Is it existing
-- Was it removed?
CREATE TABLE project_status AS
SELECT 
  CASE 
    WHEN main.name IS NOT NULL THEN main.name
    ELSE pr.name
  END AS project_slug,
  CASE
    WHEN main.name IS NOT NULL AND pr.name IS NOT NULL THEN 
      CASE
        WHEN main.name != pr.name THEN 'UPDATED'
        ELSE 'EXISTING'
      END
    WHEN main.name IS NOT NULL AND pr.name IS NULL THEN 'REMOVED'
    ELSE 'ADDED'
  END AS status
FROM main_projects AS main
FULL OUTER JOIN pr_projects AS pr
  ON main.name = pr.name