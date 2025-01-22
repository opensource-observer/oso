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
  gas,
  gas_price,
  `hash` as transaction_hash,
  from_address,
  to_address
from {{ source('optimism_superchain_raw_onchain_data', 'transactions') }}
where
  dt >= '2025-01-01'
  and network = 'mainnet'
  and receipt_status = 1
