{{
  config(
    materialized='incremental',
    partition_by={
      "field": "dt",
      "data_type": "date",
      "granularity": "day",
    },
    unique_key="id",
    on_schema_change="append_new_columns",
    incremental_strategy="insert_overwrite"
  )
}}

select
  dt,
  chain,
  gas_used,
  transaction_hash,
  from_address,
  to_address
from {{ source('optimism_superchain_raw_onchain_data', 'traces') }}
where
  dt >= '2025-01-01'
  and network = 'mainnet'
  and `status` = 1
  and call_type in ('delegatecall', 'call')
