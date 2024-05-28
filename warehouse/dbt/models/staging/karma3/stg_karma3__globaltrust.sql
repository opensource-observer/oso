{#
  Get all Karma3 EigenTrust scores
  for Farcaster IDs
#}

{{
  config(
    materialized='table',
    partition_by={
      "field": "snapshot_time",
      "data_type": "timestamp",
      "granularity": "day"
    }
  )
}}

select
  strategy_id,
  i as farcaster_id,
  CAST(v as numeric) as eigentrust_rank,
  CAST(date as timestamp) as snapshot_time
from {{ source("karma3", "globaltrust") }}
