CREATE TABLE {{ source }}_blockchain_artifacts AS
SELECT DISTINCT
  p.name AS project_name,
  LOWER(blockchains.unnest.address) AS address,
  tag.unnest AS tag,
  network.unnest AS network
FROM {{ source }}_projects AS p 
CROSS JOIN UNNEST(p.blockchain) AS blockchains
CROSS JOIN UNNEST(blockchains.unnest.networks) AS network
CROSS JOIN UNNEST(blockchains.unnest.tags) AS tag
