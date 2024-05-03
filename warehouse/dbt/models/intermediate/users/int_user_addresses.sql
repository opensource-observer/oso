{# 
  This model is a WIP and is not yet ready for production use.
#}

with user_data as (
  select
    from_id,
    MAX(rfm_recency) as r,
    MAX(rfm_frequency) as f,
    MAX(rfm_ecosystem) as e
  from {{ ref('int_address_rfm_segments_by_project') }}
  group by 1
)

select
  from_id as user_id,
  (r > 2 and f > 2 and e > 2) as is_trusted
from user_data
