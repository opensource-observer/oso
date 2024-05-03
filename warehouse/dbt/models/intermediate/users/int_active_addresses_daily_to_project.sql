{#
  Daily active addresses to project by network
#}


select
  project_id,
  from_namespace as network,
  bucket_day,
  address_type as user_type,
  COUNT(distinct from_id) as amount
from {{ ref('int_addresses_daily_activity') }}
group by 1, 2, 3, 4
