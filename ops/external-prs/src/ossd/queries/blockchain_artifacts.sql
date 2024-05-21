CREATE TABLE {{ source }}_blockchain_artifacts AS
SELECT DISTINCT
  p.name AS project_slug,
  LOWER(blockchains.blockchain.address) AS address,
  tag.tags AS tag,
  network.networks AS network
FROM {{ source }}_projects AS p 
CROSS JOIN UNNEST(p.blockchain) AS blockchains
CROSS JOIN UNNEST(blockchains.blockchain.networks) AS network
CROSS JOIN UNNEST(blockchains.blockchain.tags) AS tag
