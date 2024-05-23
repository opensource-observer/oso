{% macro factory_deployments(
    network_name, 
    traces="traces", 
    transactions_source=None, 
    transactions_table_transaction_hash_column="hash", 
    traces_table_transaction_hash_column="transaction_hash", 
    block_timestamp_column="block_timestamp") 
%}

{% if not transactions_source %}
{% set transactions_source = source(network_name, "transactions") %}
{% endif %}
{% set transactions_table_hash_value = "`txs`.`%s`" % (
    transactions_table_transaction_hash_column,
  )
%}
{% set traces_table_hash_value = "`traces`.`%s`" % (
    traces_table_transaction_hash_column,
  )
%}
{% set aliased_block_timestamp_column = "`traces`.%s" % (
    block_timestamp_column,
  )
%}

WITH transactions AS (
  SELECT *
  FROM {{ transactions_source }}
  {% if is_incremental() %}
  WHERE {{ block_timestamp_column }} > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
  {% else %}
  {{ playground_filter(block_timestamp_column, is_start=True) }}
  {% endif %}
)

select 
  traces.block_timestamp, 
  traces.transaction_hash, 
  {# this is the eoa that triggered the request #}
  txs.from_address as originating_address, 
  {# 
    It is possible for originating_contract and factory address to be the same.
    In the case of something like a safe, the originating_contract would be the
    safe.
  #}
  txs.to_address as originating_contract,
  traces.from_address as factory_address, 
  traces.to_address as contract_address
from {{ source(network_name, traces) }} as traces
inner join transactions as txs
  on {{ transactions_table_hash_value }} = {{ traces_table_hash_value }}

WHERE LOWER(trace_type) in ("create", "create2") and status = 1
{% if is_incremental() %}
  and {{ aliased_block_timestamp_column }} > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
{% else %}
{{ playground_filter(aliased_block_timestamp_column, is_start=False) }}
{% endif %}

{% endmacro %}