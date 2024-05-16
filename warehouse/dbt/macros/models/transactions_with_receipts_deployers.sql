{#
  Mostly for the goldsky data transactions which include receipt data. This
  discovers deployers on a given network.
#}

{% macro transactions_with_receipts_deployers(network_name) %}

{% if target.name == 'production' %}
SELECT
  block_timestamp AS block_timestamp,
  `hash` AS transaction_hash,
  from_address AS deployer_address,
  receipt_contract_address AS contract_address
FROM {{ source(network_name, "transactions") }}
WHERE
  to_address IS null
  AND `receipt_status` = 1
  {% if is_incremental() %}
  AND block_timestamp > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
  {% else %}
  {{ playground_filter("block_timestamp", is_start=False) }}
  {% endif %}
{% else %}
select 
  *
from {{ source("base_playground", "%s_deployers" % network_name) }}
{% if is_incremental() %}
where block_timestamp > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
  {{ playground_filter("block_timestamp", is_start=False) }}
{% else %}
{{ playground_filter("block_timestamp") }}
{% endif %}

{% endif %}
{% endmacro %}
