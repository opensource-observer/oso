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

with base_traces as (
  {{ filtered_blockchain_events("BASE", "base", "traces") }}
),

transformed_traces as (
  select
    *,
    CAST(`value` as FLOAT64) as numeric_value
  from base_traces
)

select
  * except (`value`, numeric_value),
  numeric_value as `value`
from transformed_traces
