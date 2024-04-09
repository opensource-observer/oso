-- Get the status of a project based on it's slug.
-- Is it an entirely new project?
-- Is it existing
-- Was it removed?
CREATE TABLE code_status AS
SELECT 
  CASE 
    WHEN main.code_url IS NOT NULL THEN main.project_slug
    ELSE pr.project_slug
  END AS project_slug,
  CASE 
    WHEN main.code_url IS NOT NULL THEN main.code_url
    ELSE pr.code_url
  END AS code_url,
  CASE
    WHEN main.project_slug IS NOT NULL AND pr.project_slug IS NOT NULL THEN 'EXISTING'
    WHEN main.project_slug IS NOT NULL AND pr.project_slug IS NULL THEN 'REMOVED'
    ELSE 'ADDED'
  END AS status
FROM main_code_artifacts AS main
FULL OUTER JOIN pr_code_artifacts AS pr
  ON main.project_slug = pr.project_slug AND main.code_url = pr.code_url