{{
  config(
    materialized='incremental',
    partition_by={
      "field": "date_timestamp",
      "data_type": "timestamp",
      "granularity": "day",
    },
    unique_id=["address", "date_timestamp"],
    on_schema_change="append_new_columns",
    incremental_strategy="insert_overwrite"
  ) 
}}

{{ addresses_daily_gas_and_usage("pgn") }}
