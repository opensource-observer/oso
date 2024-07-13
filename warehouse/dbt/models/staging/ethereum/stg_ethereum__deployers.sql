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
  )
}}

{% if target.name == 'production' %}
select
  block_timestamp,
  `hash` as transaction_hash,
  from_address as deployer_address,
  receipt_contract_address as contract_address
from {{ source("ethereum", "transactions") }}
where
  to_address is null
  and receipt_status = 1
  and receipt_contract_address is not null
  {% if is_incremental() %}
    AND block_timestamp > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
    {{ playground_filter("block_timestamp", is_start=False) }}
  {% else %}
  {{ playground_filter("block_timestamp", is_start=False) }}
  {% endif %}
{% else %}
  select *
  from {{ source(current_playground(), "ethereum_deployers") }}
  {% if is_incremental() %}
    where
      block_timestamp > TIMESTAMP_SUB(_dbt_max_partition, interval 1 day)
      {{ playground_filter("block_timestamp", is_start=False) }}
  {% endif %}
{% endif %}
