{{
  config(
    materialized='incremental',
    partition_by={
      "field": "block_timestamp",
      "data_type": "timestamp",
      "granularity": "day",
    },
    unique_id="id",
    on_schema_change="append_new_columns",
    incremental_strategy="insert_overwrite"
  ) if target.name == 'production' else config(
    materialized='table',
  )
}}
with known_addresses as (
  select distinct `artifact_source_id` as `address`
  from {{ ref("int_artifacts_by_project") }}
  where `artifact_source` = 'OPTIMISM'
),

receipts as (
  select *
  from {{ oso_source("optimism", "receipts") }}
  {% if is_incremental() %}
  where block_timestamp > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
  {% endif %}
)

select
  transactions.*,
  receipts.contract_address as receipt_contract_address,
  receipts.cumulative_gas_used as receipt_cumulative_gas_used,
  receipts.gas_used as receipt_gas_used,
  receipts.effective_gas_price as receipt_effective_gas_price,
  receipts.root as receipt_root,
  receipts.status as receipt_status
from {{ oso_source("optimism", "transactions") }} as transactions
inner join receipts as receipts
  on transactions.transaction_hash = receipts.transaction_hash
where
  transactions.to_address in (select * from known_addresses)
  or transactions.from_address in (select * from known_addresses)
{% if is_incremental() %}
    {# 
      We are using insert_overwrite so this will consistently select everything
      that would go into the latest partition (and any new partitions after
      that). It will overwrite any data in the partitions for which this select
      statement matches
    #}
    and block_timestamp > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
  {% endif %}
