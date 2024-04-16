{#
  Using goog_blockchain_* public tables, this discovers deployers on a given network.
#}

{% macro goog_blockchain_deployers(network_name) %}
WITH {% if is_incremental() %} max_block_timestamp AS  (
  {# If there's no existing max time then we arbitrarily query at unix time 0 #}
  SELECT COALESCE(MAX(block_timestamp), '1970-01-01')  as ts
  FROM {{ this }}
),
{% endif %}
logs AS (
  -- transactions
  SELECT *
  FROM {{ oso_source(network_name, "logs") }}
  {% if is_incremental() %}
  WHERE 
    block_timestamp >= (
      SELECT * FROM max_block_timestamp
    )
    AND block_timestamp < TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), DAY)
  {% endif %}
)

SELECT
  t.block_timestamp AS block_timestamp,
  t.transaction_hash AS transaction_hash,
  t.from_address AS deployer_address,
  l.address AS contract_address
FROM {{ oso_source(network_name, "transactions") }} AS t
INNER JOIN logs AS l
  ON t.transaction_hash = l.transaction_hash
WHERE
  t.to_address IS null
  {% if is_incremental() %}
  AND t.block_timestamp >= (
    SELECT * FROM max_block_timestamp
  )
  AND t.block_timestamp < TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), DAY)
  {% endif %}
{% endmacro %}
