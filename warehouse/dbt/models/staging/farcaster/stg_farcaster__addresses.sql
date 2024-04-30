{#
  Get all verified addresses attached to an FID
#}

SELECT
  v.fid AS fid,
  v.address AS address
FROM {{ source("farcaster", "farcaster_verifications") }} AS v
WHERE v.deleted_at IS NULL
