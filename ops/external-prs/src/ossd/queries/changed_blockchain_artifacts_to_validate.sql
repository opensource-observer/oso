WITH grouped_pr_addresses AS (
  SELECT
    b.address,
    ARRAY_AGG(DISTINCT b.tag) AS tags,
    ARRAY_AGG(DISTINCT b.network) AS networks,
  FROM pr_blockchain_artifacts AS b
  GROUP BY 1
)
SELECT 
  b.address,
  b.tags,
  b.networks
FROM grouped_pr_addresses AS b
WHERE 'ADDED' IN ((
  SELECT project_relation_status
  FROM blockchain_status
  WHERE address = b.address
))