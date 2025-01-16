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
), url_changes_summary AS (
  SELECT 
    s.url_type AS "type",
    s.status AS "status",
    COUNT(*) AS "count",
    COUNT(*) AS "unique_count"
  FROM url_status AS s
  GROUP BY 1,2
)
SELECT * FROM blockchain_changes_summary
UNION ALL
SELECT * FROM url_changes_summary