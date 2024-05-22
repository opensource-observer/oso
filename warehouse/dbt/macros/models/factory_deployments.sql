{% macro factory_deployments(network_name, traces="traces") %}
SELECT block_timestamp, transaction_hash, from_address as factory_address, to_address as contract_address,  
FROM {{ source(network_name, traces) }}

WHERE LOWER(trace_type) in ("create", "create2") and status = 1
{% if is_incremental() %}
  and block_timestamp > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
{% else %}
{{ playground_filter("block_timestamp", is_start=False) }}
{% endif %}

{% endmacro %}