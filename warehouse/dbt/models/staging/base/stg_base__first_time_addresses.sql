{{
  config(
    materialized='incremental',
    partition_by={
      "field": "first_block_timestamp",
      "data_type": "timestamp",
      "granularity": "day",
    },
    unique_id="address",
    on_schema_change="append_new_columns",
    incremental_strategy="insert_overwrite"
  ) 
}}
{{ first_time_addresses("base") }}
