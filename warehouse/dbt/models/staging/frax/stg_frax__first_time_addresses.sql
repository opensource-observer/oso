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

{% set unique_key_col = config.get('unique_id') %}

{{ first_time_addresses("frax") }}
{% if is_incremental() %}
  where
    {{ unique_key_col }} not in (select {{ unique_key_col }} from {{ this }})
{% endif %}
