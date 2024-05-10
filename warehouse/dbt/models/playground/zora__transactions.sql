{{
  config(
    materialized='table',
  ) if target.name in ['playground', 'dev'] else config(
    enabled=false,
  )
}}
select *
from {{ source('zora', 'transactions') }}
where block_timestamp >= TIMESTAMP_TRUNC(
  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), interval 1 day),
  day
)
