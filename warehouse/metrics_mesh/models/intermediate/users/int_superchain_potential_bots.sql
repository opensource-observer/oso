MODEL (
  name metrics.int_superchain_potential_bots,
  kind FULL,
  enabled false,
);

with union_queries (
  select
    lower(address) as address,
    upper(chain_name) as network
  from metrics.stg_superchain__potential_bots
)

select distinct
  @oso_id(network, address) as artifact_id,
  address,
  network
from union_queries
