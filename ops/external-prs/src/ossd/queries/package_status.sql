-- Get the status of a project based on it's slug.
-- Is it an entirely new project?
-- Is it existing
-- Was it removed?
CREATE TABLE package_status AS
SELECT 
  CASE 
    WHEN main.package_url IS NOT NULL THEN main.project_slug
    ELSE pr.project_slug
  END AS project_slug,
  CASE 
    WHEN main.package_url IS NOT NULL THEN main.package_url
    ELSE pr.package_url
  END AS package_url,
  CASE
    WHEN main.project_slug IS NOT NULL AND pr.project_slug IS NOT NULL THEN 'EXISTING'
    WHEN main.project_slug IS NOT NULL AND pr.project_slug IS NULL THEN 'REMOVED'
    ELSE 'ADDED'
  END AS status
FROM main_package_artifacts AS main
FULL OUTER JOIN pr_package_artifacts AS pr
  ON main.project_slug = pr.project_slug AND main.package_url = pr.package_url