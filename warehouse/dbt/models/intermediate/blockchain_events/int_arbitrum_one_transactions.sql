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
    incremental_strategy="insert_overwrite",
    sql_header='''
CREATE TEMP FUNCTION from_string_to_double(input STRING)
RETURNS FLOAT64
LANGUAGE js AS r"""
    yourNumber = BigInt(input, 10);
    return parseFloat(yourNumber);
  """;
    '''
  )
}}

with filtered_transactions as (
  {{ filtered_blockchain_events("ARBITRUM_ONE", "arbitrum_one", "transactions") }}
)
select 
  id,
  `hash`,
  nonce,
  block_hash,
  block_number,
  transaction_index,
  from_address,
  to_address,
  `value`,
  gas,
  -- We need to convert the arbitrum gas_price from bytes to a double. We
  -- intentionally lose some precision by doing this. The gas_price is 
  -- actually a utf-8 string. So we convert this to a string which is a string of the integer
  from_string_to_double(CAST(gas_price AS STRING FORMAT 'UTF-8')) as gas_price,
  input,
  max_fee_per_gas,
  max_priority_fee_per_gas,
  transaction_type,
  receipt_cumulative_gas_used,
  receipt_gas_used,
  receipt_contract_address,
  receipt_status,
  receipt_effective_gas_price,
  receipt_root_hash,
  receipt_l1_fee,
  receipt_l1_gas_used,
  receipt_l1_gas_price,
  receipt_l1_fee_scalar,
  receipt_l1_blob_base_fee,
  receipt_l1_blob_base_fee_scalar,
  blob_versioned_hashes,
  max_fee_per_blob_gas,
  receipt_l1_block_number,
  receipt_l1_base_fee_scalar,
  gateway_fee,
  fee_currency,
  gateway_fee_recipient,
  ingestion_time,
  block_timestamp
from filtered_transactions
