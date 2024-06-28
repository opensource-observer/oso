{{ config(
    materialized='table',
    partition_by={
      "field": "airdrop_round",
      "data_type": "int64",
      "range": {
        "start": 0,
        "end": 100,
        "interval": 10
      }
    }
) }}

{{
  combine_op_airdrops(generate_range(1, 4))
}}
