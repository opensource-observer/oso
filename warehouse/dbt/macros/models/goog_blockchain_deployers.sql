{#
  Using goog_blockchain_* public tables, this discovers deployers on a given network.
#}

{% macro goog_blockchain_deployers(network_name) %}
{% if is_incremental() %} 
WITH max_block_timestamp AS  (
  {# If there's no existing max time then we arbitrarily query at unix time 0 #}
  SELECT COALESCE(MAX(block_timestamp), '1970-01-01')  as ts
  FROM {{ this }}
)
{% endif %}

SELECT
  block_timestamp AS block_timestamp,
  transaction_hash AS transaction_hash,
  from_address AS deployer_address,
  contract_address AS contract_address
FROM {{ oso_source(network_name, "receipts") }}
WHERE
  to_address IS null
  AND `status` = 1
  {% if is_incremental() %}
  AND block_timestamp >= (
    SELECT * FROM max_block_timestamp
  )
  AND block_timestamp < TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), DAY)
  {% endif %}
{% endmacro %}
