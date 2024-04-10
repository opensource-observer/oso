-- Get project
CREATE TABLE artifacts_summary AS
WITH blockchain_changes_summary AS (
  SELECT 
    'BLOCKCHAIN' AS "type",
    bs.project_relation_status AS "status",
    COUNT(*) AS "count",
    COUNT(DISTINCT bs.address) AS "unique_count"
  FROM blockchain_status AS bs
  GROUP BY 1,2
), code_changes_summary AS (
  SELECT 
    'CODE' AS "type",
    s.status AS "status",
    COUNT(*) AS "count",
    COUNT(*) AS "unique_count"
  FROM code_status AS s
  GROUP BY 1,2
), package_changes_summary AS (
  SELECT 
    'PACKAGE' AS "type",
    s.status AS "status",
    COUNT(*) AS "count",
    COUNT(*) AS "unique_count"
  FROM package_status AS s
  GROUP BY 1,2
)
SELECT * FROM blockchain_changes_summary
UNION ALL
SELECT * FROM code_changes_summary
UNION ALL
SELECT * FROM package_changes_summary