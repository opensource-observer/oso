{#
  Get all farcaster profiles from the JSON
#}

select
  profiles.fid as fid,
  profiles.custody_address as custody_address,
  JSON_EXTRACT(profiles.data, "$.username") as username,
  JSON_EXTRACT(profiles.data, "$.display") as display_name,
  JSON_EXTRACT(profiles.data, "$.pfp") as profile_picture_url,
  JSON_EXTRACT(profiles.data, "$.bio") as bio,
  JSON_EXTRACT(profiles.data, "$.url") as url
from {{ source("farcaster", "farcaster_profiles") }} as profiles
