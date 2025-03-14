MODEL (
  name oso.int_proxies,
  kind FULL
);

WITH superchain_proxies AS (
  SELECT
    LOWER(to_address) AS address,
    LOWER(proxy_address) AS proxy_address,
    UPPER(chain) AS chain,
    MIN(block_timestamp) AS created_date
  FROM oso.stg_superchain__proxies
  WHERE
    proxy_address <> to_address
  GROUP BY
    to_address,
    proxy_address,
    chain
)
SELECT
  @oso_id(chain, '', address) AS artifact_id,
  address,
  proxy_address,
  chain,
  created_date
FROM superchain_proxies