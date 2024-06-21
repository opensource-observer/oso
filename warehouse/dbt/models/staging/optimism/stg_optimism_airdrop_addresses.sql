{{
  config(
    materialized="incremental",
    partition_by="airdrop_round",
    unique_key="concat(airdrop_round, address)",
    on_schema_change="append_new_columns",
    incremental_strategy="insert_overwrite"
  )
}}

{{
  combine_op_airdrops(generate_range(1, 4))
}}
