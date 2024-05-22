{#
  Get all Karma3 EigenTrust scores
  for Farcaster IDs
#}

select
  strategy_id,
  CAST(i as string) as farcaster_id,
  CAST(v as numeric) as eigentrust_rank,
  CAST(date as timestamp) as date
from {{ source("karma3", "localtrust") }}
