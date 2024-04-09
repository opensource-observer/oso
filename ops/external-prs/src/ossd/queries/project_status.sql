-- Get the status of a project based on it's slug.
-- Is it an entirely new project?
-- Is it existing
-- Was it removed?
CREATE TABLE project_status AS
SELECT 
  CASE 
    WHEN main.slug IS NOT NULL THEN main.slug
    ELSE pr.slug
  END AS project_slug,
  CASE
    WHEN main.slug IS NOT NULL AND pr.slug IS NOT NULL THEN 
      CASE
        WHEN main.name != pr.name THEN 'UPDATED'
        ELSE 'EXISTING'
      END
    WHEN main.slug IS NOT NULL AND pr.slug IS NULL THEN 'REMOVED'
    ELSE 'ADDED'
  END AS status
FROM main_projects AS main
FULL OUTER JOIN pr_projects AS pr
  ON main.slug = pr.slug