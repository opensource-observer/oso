{#
  Mostly for the goldsky data transactions which include receipt data. This
  discovers deployers on a given network.
#}

{% macro transactions_with_receipts_deployers(network_name) %}

SELECT
  block_timestamp AS block_timestamp,
  `hash` AS transaction_hash,
  from_address AS deployer_address,
  receipt_contract_address AS contract_address
FROM {{ oso_source(network_name, "transactions") }}
WHERE
  to_address IS null
  AND `receipt_status` = 1
  {% if is_incremental() %}
  AND block_timestamp > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
  {% endif %}
{% endmacro %}
