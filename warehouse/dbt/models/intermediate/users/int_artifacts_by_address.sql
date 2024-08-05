with addresses as (
  select distinct
    LOWER(address) as address,
    UPPER(chain_name) as chain
  from {{ ref('int_first_time_addresses') }}
)

select
  {{ oso_id("chain", "address") }} as artifact_id,
  chain as artifact_namespace,
  address as artifact_name
from addresses
