{#
  Get all Karma3 EigenTrust scores
  for Farcaster IDs - Local Trust
#}

{{
  config(
    materialized='table',
    partition_by={
      "field": "farcaster_id",
      "data_type": "int64",
      "range": {
        "start": 0,
        "end": 1000000,
        "interval": 25000
      }
    }
  )
}}

select
  strategy_id,
  i as farcaster_id,
  j as peer_farcaster_id,
  CAST(v as numeric) as eigentrust_rank,
  CAST(date as timestamp) as snapshot_time
from {{ source("karma3", "localtrust") }}
