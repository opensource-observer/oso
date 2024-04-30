{#
  Get all farcaster profiles from the JSON
#}

SELECT
  profiles.fid AS fid,
  profiles.custody_address AS custody_address,
  JSON_EXTRACT(profiles.data, "$.username") AS username,
  JSON_EXTRACT(profiles.data, "$.display") AS display_name,
  JSON_EXTRACT(profiles.data, "$.pfp") AS profile_picture_url,
  JSON_EXTRACT(profiles.data, "$.bio") AS bio,
  JSON_EXTRACT(profiles.data, "$.url") AS url
FROM {{ source("farcaster", "farcaster_profiles") }} AS profiles
