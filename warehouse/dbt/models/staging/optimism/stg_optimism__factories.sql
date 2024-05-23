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
{{ 
  factory_deployments(
    "superchain", 
    traces="optimism_traces",
    transactions_source=oso_source("optimism", "transactions"),
    transactions_table_transaction_hash_column="transaction_hash",
  ) 
}}
