-- Get project
CREATE TABLE project_summary AS
WITH blockchain_changes_summary AS (
  SELECT 
    bs.project_slug as project_slug,
    bs.project_relation_status AS "status",
    COUNT(*) AS "count",
    COUNT(DISTINCT bs.address) AS "unique_count"
  FROM blockchain_status AS bs
  GROUP BY 1,2
), code_changes_summary AS (
  SELECT 
    s.project_slug as project_slug,
    s.status AS "status",
    COUNT(*) AS "count"
  FROM code_status AS s
  GROUP BY 1,2
), package_changes_summary AS (
  SELECT 
    s.project_slug as project_slug,
    s.status AS "status",
    COUNT(*) AS "count"
  FROM package_status AS s
  GROUP BY 1,2
)
SELECT 
  ps.project_slug,
  ps.status, -- for metadata changes
  COALESCE(
    (
      SELECT b."count"
      FROM blockchain_changes_summary AS b
      WHERE 
        b.project_slug = ps.project_slug
        AND b."status" = 'ADDED'
    ),
    0
  ) as blockchain_added,
  COALESCE(
    (
      SELECT b."unique_count"
      FROM blockchain_changes_summary AS b
      WHERE 
        b.project_slug = ps.project_slug
        AND b."status" = 'ADDED'
    ),
    0
  ) as blockchain_unique_added,
  COALESCE(
    (
      SELECT b."count"
      FROM blockchain_changes_summary AS b
      WHERE 
        b.project_slug = ps.project_slug 
        AND b."status" = 'REMOVED'
    ),
    0
  ) as blockchain_removed,
  COALESCE(
    (
      SELECT b."unique_count"
      FROM blockchain_changes_summary AS b
      WHERE 
        b.project_slug = ps.project_slug
        AND b."status" = 'REMOVED'
    ),
    0
  ) as blockchain_unique_removed,
  COALESCE(
    (
      SELECT b."count"
      FROM blockchain_changes_summary AS b
      WHERE 
        b.project_slug = ps.project_slug
        AND b."status" = 'EXISTING'
    ),
    0
  ) as blockchain_unchanged,
  COALESCE(
    (
      SELECT b."unique_count"
      FROM blockchain_changes_summary AS b
      WHERE 
        b.project_slug = ps.project_slug
        AND b."status" = 'EXISTING'
    ),
    0
  ) as blockchain_unique_unchanged,
  COALESCE(
    (
      SELECT b."count"
      FROM blockchain_changes_summary AS b
      WHERE 
        b.project_slug = ps.project_slug
        AND b."status" = 'EXISTING'
    ),
    0
  ) as blockchain_unchanged,
  COALESCE(
    (
      SELECT c."count"
      FROM code_changes_summary AS c
      WHERE 
        c.project_slug = ps.project_slug
        AND c."status" = 'ADDED'
    ),
    0
  ) as code_added,
  COALESCE(
    (
      SELECT c."count"
      FROM code_changes_summary AS c
      WHERE 
        c.project_slug = ps.project_slug
        AND c."status" = 'REMOVED'
    ),
    0
  ) as code_removed,
  COALESCE(
    (
      SELECT c."count"
      FROM code_changes_summary AS c
      WHERE 
        c.project_slug = ps.project_slug
        AND c."status" = 'EXISTING'
    ),
    0
  ) as code_unchanged,
  COALESCE(
    (
      SELECT p."count"
      FROM package_changes_summary as p
      WHERE 
        p.project_slug = ps.project_slug
        AND p."status" = 'ADDED'
    ),
    0
  ) AS package_added,
  COALESCE(
    (
      SELECT p."count"
      FROM package_changes_summary as p
      WHERE 
        p.project_slug = ps.project_slug
        AND p."status" = 'REMOVED'
    ),
    0
  ) AS package_removed,
  COALESCE(
    (
      SELECT p."count"
      FROM package_changes_summary as p
      WHERE 
        p.project_slug = ps.project_slug
        AND p."status" = 'EXISTING'
    ),
    0
  ) AS package_unchanged
FROM project_status AS ps