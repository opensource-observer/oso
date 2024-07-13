{{ config(
    enabled=target.name == 'production',
    materialized='table',
    partition_by={
      "field": "min_block_time",
      "data_type": "timestamp",
      "granularity": "day",
    },
) }}

{{
  potential_bots("ethereum")
}}
