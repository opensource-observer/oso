-- Get project
CREATE TABLE project_summary AS
WITH blockchain_changes_summary AS (
  SELECT 
    bs.project_name as project_name,
    bs.project_relation_status AS "status",
    COUNT(*) AS "count",
    COUNT(DISTINCT bs.address) AS "unique_count"
  FROM blockchain_status AS bs
  GROUP BY 1,2
), url_changes_summary AS (
  SELECT 
    s.project_name as project_name,
    s.status AS "status",
    COUNT(*) AS "count"
  FROM url_status AS s
  GROUP BY 1,2
)
SELECT 
  ps.project_name,
  ps.status, -- for metadata changes
  COALESCE(
    (
      SELECT b."count"
      FROM blockchain_changes_summary AS b
      WHERE 
        b.project_name = ps.project_name
        AND b."status" = 'ADDED'
    ),
    0
  ) as blockchain_added,
  COALESCE(
    (
      SELECT b."unique_count"
      FROM blockchain_changes_summary AS b
      WHERE 
        b.project_name = ps.project_name
        AND b."status" = 'ADDED'
    ),
    0
  ) as blockchain_unique_added,
  COALESCE(
    (
      SELECT b."count"
      FROM blockchain_changes_summary AS b
      WHERE 
        b.project_name = ps.project_name 
        AND b."status" = 'REMOVED'
    ),
    0
  ) as blockchain_removed,
  COALESCE(
    (
      SELECT b."unique_count"
      FROM blockchain_changes_summary AS b
      WHERE 
        b.project_name = ps.project_name
        AND b."status" = 'REMOVED'
    ),
    0
  ) as blockchain_unique_removed,
  COALESCE(
    (
      SELECT b."count"
      FROM blockchain_changes_summary AS b
      WHERE 
        b.project_name = ps.project_name
        AND b."status" = 'EXISTING'
    ),
    0
  ) as blockchain_unchanged,
  COALESCE(
    (
      SELECT b."unique_count"
      FROM blockchain_changes_summary AS b
      WHERE 
        b.project_name = ps.project_name
        AND b."status" = 'EXISTING'
    ),
    0
  ) as blockchain_unique_unchanged,
  COALESCE(
    (
      SELECT b."count"
      FROM blockchain_changes_summary AS b
      WHERE 
        b.project_name = ps.project_name
        AND b."status" = 'EXISTING'
    ),
    0
  ) as blockchain_unchanged,
  COALESCE(
    (
      SELECT c."count"
      FROM url_changes_summary AS c
      WHERE 
        c.project_name = ps.project_name
        AND c."status" = 'ADDED'
    ),
    0
  ) as url_added,
  COALESCE(
    (
      SELECT c."count"
      FROM url_changes_summary AS c
      WHERE 
        c.project_name = ps.project_name
        AND c."status" = 'REMOVED'
    ),
    0
  ) as url_removed,
  COALESCE(
    (
      SELECT c."count"
      FROM url_changes_summary AS c
      WHERE 
        c.project_name = ps.project_name
        AND c."status" = 'EXISTING'
    ),
    0
  ) as url_unchanged
FROM project_status AS ps