{#
  Using goog_blockchain_* public tables, this discovers deployers on a given network.
#}

{% macro goog_blockchain_deployers(network_name) %}
{% if target.name == 'production' %}
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
  AND block_timestamp > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
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
