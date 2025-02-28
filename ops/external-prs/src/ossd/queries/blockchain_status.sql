CREATE TABLE blockchain_status AS
WITH address_by_tag_by_network_by_project_status AS (
  SELECT 
    CASE
      WHEN main.address IS NOT NULL THEN main.project_name
      ELSE pr.project_name
    END as project_name,
    CASE 
      WHEN main.address IS NOT NULL THEN main.address
      ELSE pr.address
    END AS address,
    CASE
      WHEN main.address IS NOT NULL THEN main.tag
      ELSE pr.tag
    END AS tag,
    CASE
      WHEN main.address IS NOT NULL THEN main.network
      ELSE pr.network
    END AS network,
    CASE
      WHEN main.address IS NOT NULL AND pr.address IS NOT NULL THEN 'EXISTING'
      WHEN main.address IS NOT NULL AND pr.address IS NULL THEN 'REMOVED'
      WHEN main.address IS NULL AND pr.address IS NOT NULL THEN 'ADDED'
      WHEN main.address IS NULL AND pr.address IS NULL THEN 'IGNORED'
      ELSE 'UNKNOWN'
    END AS status
  FROM main_blockchain_artifacts AS main
  FULL OUTER JOIN pr_blockchain_artifacts AS pr
    ON main.project_name = pr.project_name AND main.address = pr.address AND main.tag = pr.tag AND main.network = pr.network
), address_by_tag_by_network_status AS (
  SELECT 
    CASE 
      WHEN main.address IS NOT NULL THEN main.address
      ELSE pr.address
    END AS address,
    CASE
      WHEN main.address IS NOT NULL THEN main.tag
      ELSE pr.tag
    END AS tag,
    CASE
      WHEN main.address IS NOT NULL THEN main.network
      ELSE pr.network
    END AS network,
    CASE
      WHEN main.address IS NOT NULL AND pr.address IS NOT NULL THEN 'EXISTING'
      WHEN main.address IS NOT NULL AND pr.address IS NULL THEN 'REMOVED'
      ELSE 'ADDED'
    END AS status
  FROM main_blockchain_artifacts AS main
  FULL OUTER JOIN pr_blockchain_artifacts AS pr
    ON main.address = pr.address AND main.tag = pr.tag AND main.network = pr.network
), address_by_tag AS (
  SELECT
    CASE 
      WHEN main.address IS NOT NULL THEN main.address
      ELSE pr.address
    END AS address,
    CASE
      WHEN main.address IS NOT NULL THEN main.tag
      ELSE pr.tag
    END AS tag,
    CASE
      WHEN main.address IS NOT NULL AND pr.address IS NOT NULL THEN 'EXISTING'
      WHEN main.address IS NOT NULL AND pr.address IS NULL THEN 'REMOVED'
      ELSE 'ADDED'
    END AS status
  FROM main_blockchain_artifacts AS main
  FULL OUTER JOIN pr_blockchain_artifacts AS pr
    ON main.address = pr.address AND main.network = pr.network
), address_by_network AS (
  SELECT
    CASE 
      WHEN main.address IS NOT NULL THEN main.address
      ELSE pr.address
    END AS address,
    CASE
      WHEN main.address IS NOT NULL THEN main.network
      ELSE pr.network
    END AS network,
    CASE
      WHEN main.address IS NOT NULL AND pr.address IS NOT NULL THEN 'EXISTING'
      WHEN main.address IS NOT NULL AND pr.address IS NULL THEN 'REMOVED'
      ELSE 'ADDED'
    END AS status
  FROM main_blockchain_artifacts AS main
  FULL OUTER JOIN pr_blockchain_artifacts AS pr
    ON main.address = pr.address AND main.network = pr.network
), address_status AS (
  SELECT
    CASE 
      WHEN main.address IS NOT NULL THEN main.address
      ELSE pr.address
    END AS address,
    CASE
      WHEN main.address IS NOT NULL AND pr.address IS NOT NULL THEN 'EXISTING'
      WHEN main.address IS NOT NULL AND pr.address IS NULL THEN 'REMOVED'
      ELSE 'ADDED'
    END AS status
  FROM main_blockchain_artifacts AS main
  FULL OUTER JOIN pr_blockchain_artifacts AS pr
    ON main.address = pr.address
)
SELECT
  by_project.project_name,
  by_project.address,
  by_project.tag,
  by_project.network,
  by_project.status AS project_relation_status,
  by_addr.status AS address_status,
  by_network.status AS network_status,
  by_network_and_tag.status AS network_tag_status
FROM address_by_tag_by_network_by_project_status AS by_project
INNER JOIN address_by_tag_by_network_status AS by_network_and_tag
  ON 
    by_project.address = by_network_and_tag.address 
    AND by_project.tag = by_network_and_tag.tag
    AND by_project.network = by_network_and_tag.network
INNER JOIN address_by_network AS by_network
  ON 
    by_project.address = by_network.address 
    AND by_project.network = by_network.network
INNER JOIN address_status AS by_addr
  ON 
    by_project.address = by_addr.address
