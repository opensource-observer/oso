{#
  Get all verified addresses attached to an FID
#}

select
  v.fid as fid,
  v.address as address
from {{ source("farcaster", "farcaster_verifications") }} as v
where v.deleted_at is null
