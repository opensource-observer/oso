{{ 
  config(
    materialized='table'
  )
}}

{#
  Get all verified addresses attached to an FID
#}

select
  cast(v.fid as string) as fid,
  lower(v.address) as address
from {{ source("farcaster", "farcaster_verifications") }} as v
where v.deleted_at is null
