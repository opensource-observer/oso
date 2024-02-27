{{
  config(
    materialized='table',
  ) if target.name in ['playground', 'dev'] else config(
    enabled=false,
  )
}}
{# Only get the last 3 months of contract events #}
SELECT * 
FROM {{ source('dune', 'arbitrum_contract_usage') }}
WHERE date >= DATE_ADD(CURRENT_DATE(), INTERVAL -3 MONTH)