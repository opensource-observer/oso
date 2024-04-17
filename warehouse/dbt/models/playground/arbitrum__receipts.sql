{{
  config(
    materialized='table',
  ) if target.name in ['playground', 'dev'] else config(
    enabled=false,
  )
}}
SELECT *
FROM {{ source("arbitrum", 'receipts') }}
WHERE block_timestamp >= TIMESTAMP_TRUNC(
  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL -14 DAY),
  DAY
)
