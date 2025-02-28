-- Get the status of a project based on it's slug.
-- Is it an entirely new project?
-- Is it existing
-- Was it removed?
CREATE TABLE url_status AS
SELECT 
  CASE 
    WHEN main.url_value IS NOT NULL THEN main.project_name
    ELSE pr.project_name
  END AS project_name,
  CASE 
    WHEN main.url_value IS NOT NULL THEN main.url_value
    ELSE pr.url_value
  END AS url_value,
  CASE 
    WHEN main.url_type IS NOT NULL THEN main.url_type
    ELSE pr.url_type
  END AS url_type,
  CASE
    WHEN main.project_name IS NOT NULL AND pr.project_name IS NOT NULL THEN 'EXISTING'
    WHEN main.project_name IS NOT NULL AND pr.project_name IS NULL THEN 'REMOVED'
    ELSE 'ADDED'
  END AS status
FROM main_url_artifacts AS main
FULL OUTER JOIN pr_url_artifacts AS pr
  ON main.project_name = pr.project_name AND
    main.url_value = pr.url_value AND
    main.url_type = pr.url_type