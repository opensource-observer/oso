{{
  config(
    materialized='table',
  ) if target.name in ['playground', 'dev'] else config(
    enabled=false,
  )
}}
{# Only get the last 3 months of contract events #}
select *
from {{ source('dune', 'optimism_contract_usage') }}
where date >= DATE_ADD(CURRENT_DATE(), interval -3 month)
