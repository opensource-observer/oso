MODEL (
  name metrics.int_proxies,
  kind FULL,
);

with superchain_proxies (
  select 
    LOWER(to_address) as address,
    LOWER(proxy_address) as proxy_address,
    UPPER(chain) as chain,
    MIN(block_timestamp) as created_date
  FROM metrics.stg_superchain__proxies
  WHERE proxy_address != to_address
  GROUP BY
    to_address,
    proxy_address,
    chain
)
select
  @oso_id(chain, address) as artifact_id,
  address,
  proxy_address,
  chain,
  created_date
from superchain_proxies