{{
  config(
    materialized='ephemeral',
  )
}}

select
  to_project_id as project_id,
  'grants_received_usd' as metric,
  amount as amount,
  'USD' as unit,
  TIMESTAMP_TRUNC(`time`, day) as sample_date
from {{ ref('int_oss_funding_grants_to_project') }}
where
  to_project_id is not null
  and amount > 0
