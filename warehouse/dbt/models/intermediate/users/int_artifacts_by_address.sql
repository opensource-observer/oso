with addresses as (
  select distinct
    UPPER(chain_name) as artifact_namespace,
    LOWER(address) as artifact_name
  from {{ ref('int_first_time_addresses') }}
)

select
  {{ oso_id("artifact_namespace", "artifact_name") }} as artifact_id,
  artifact_namespace,
  artifact_name
from addresses
