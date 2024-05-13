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
  ) 
}}
with known_addresses as (
  select distinct `artifact_source_id` as `address`
  from {{ ref("int_artifacts_by_project") }}
  where `artifact_source` = 'OPTIMISM'
),
{% if target.name == 'production' %}
receipts as (
  select *
  from {{ source("optimism", "receipts") }}
  {% if is_incremental() %}
  where block_timestamp > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
    {{ playground_filter("block_timestamp", is_start=True) }}
  {% else %}
  {{ playground_filter("block_timestamp") }}
  {% endif %}
), transactions_with_receipts as (

select
  transactions.*,
  blocks.block_number as block_number,
  receipts.contract_address as receipt_contract_address,
  receipts.cumulative_gas_used as receipt_cumulative_gas_used,
  receipts.gas_used as receipt_gas_used,
  receipts.effective_gas_price as receipt_effective_gas_price,
  receipts.root as receipt_root,
  receipts.status as receipt_status
from {{ source("optimism", "transactions") }} as transactions
inner join receipts as receipts
  on transactions.transaction_hash = receipts.transaction_hash
inner join blocks as blocks
  on transactions.block_hash = blocks.block_hash
{% if is_incremental() %}
where
    {# 
      We are using insert_overwrite so this will consistently select everything
      that would go into the latest partition (and any new partitions after
      that). It will overwrite any data in the partitions for which this select
      statement matches
    #}
    block_timestamp > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
    {{ playground_filter("block_timestamp", is_start=False) }}
{% else %}
    {{ playground_filter("block_timestamp") }}
{% endif %}
),
{% else %}
  transactions_with_receipts as (
{# 
  We need a separate query for the playground because we transform the data in
  production.
#}
    select *
    from {{ source(current_playground(), "optimism_transactions") }}
    {% if is_incremental() %}
      where
        block_timestamp > TIMESTAMP_SUB(_dbt_max_partition, interval 1 day)
        {{ playground_filter("block_timestamp", is_start=False) }}
    {% else %}
    {{ playground_filter("block_timestamp") }}
{% endif %}
  ),
{% endif %}
txs_with_dupes as (
  select txs_to.*
  from transactions_with_receipts as txs_to
  inner join known_addresses as known_to
    on txs_to.to_address = known_to.address
  union all
  select txs_from.*
  from transactions_with_receipts as txs_from
  inner join known_addresses as known_from
    on txs_from.from_address = known_from.address
)

select *
from txs_with_dupes
qualify
  ROW_NUMBER()
    over (partition by `transaction_hash` order by block_timestamp asc)
  = 1
