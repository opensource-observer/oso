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
WITH {% if is_incremental() %} max_block_timestamp AS  (
  SELECT TIMESTAMP_TRUNC(MAX(block_timestamp), DAY)
  FROM {{ this }}
),
{% endif %}
logs AS (
  -- transactions
  SELECT *
  FROM {{ oso_source("optimism", "logs") }}
  {% if is_incremental() %}
  WHERE 
    TIMESTAMP_TRUNC(block_timestamp, DAY) >= (
      SELECT * FROM max_block_timestamp
    )
    AND TIMESTAMP_TRUNC(block_timestamp, DAY) < CURRENT_TIMESTAMP()
  {% endif %}
)

SELECT
  t.block_timestamp AS block_timestamp,
  t.transaction_hash AS transaction_hash,
  t.from_address AS deployer_address,
  l.address AS contract_address
FROM {{ oso_source("optimism", "transactions") }} AS t
INNER JOIN logs AS l
  ON t.transaction_hash = l.transaction_hash
WHERE
  t.to_address IS null
  {% if is_incremental() %}
  AND TIMESTAMP_TRUNC(t.block_timestamp, DAY) >= (
    SELECT * FROM max_block_timestamp
  )
  AND TIMESTAMP_TRUNC(t.block_timestamp, DAY) < CURRENT_TIMESTAMP()
  {% endif %}
