{{
  config(
    materialized='incremental',
    partition_by={
      "field": "block_timestamp",
      "data_type": "timestamp",
      "granularity": "day",
    },
    unique_id="transaction_hash",
    on_schema_change="append_new_columns",
    incremental_strategy="insert_overwrite"
  ) if target.name == 'production' else config(
    materialized='table',
  )
}}

SELECT 
  block_timestamp,
  `hash` AS transaction_hash,
  from_address AS deployer_address, 
  receipt_contract_address AS contract_address
FROM {{ source("ethereum", "transactions") }} 
WHERE to_address IS NULL 
  AND receipt_status = 1 
  AND receipt_contract_address IS NOT NULL
  {% if is_incremental() %}
  WHERE 
    TIMESTAMP_TRUNC(block_timestamp, DAY) >= (
      SELECT TIMESTAMP_TRUNC(MAX(block_timestamp), DAY)
      FROM {{ this }}
    )
    AND TIMESTAMP_TRUNC(block_timestamp, DAY) < CURRENT_TIMESTAMP()
  {% endif %}
