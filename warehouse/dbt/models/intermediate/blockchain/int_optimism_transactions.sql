{{
  config(
    materialized='incremental',
    partition_by={
      "field": "created_at",
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
{{ ossd_filtered_blockchain_events("OPTIMISM", "optimism", "transactions") }}
