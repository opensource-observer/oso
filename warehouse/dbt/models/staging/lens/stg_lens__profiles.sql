{#
  Get all profile_ids mapped to the owner address and profile metadata
#}

SELECT
  profiles.profile_id AS profile_id,
  profiles.name AS full_name,
  profiles.bio AS bio,
  profiles.profile_picture_snapshot_location_url AS profile_picture_url,
  profiles.cover_picture_snapshot_location_url AS cover_picture_url
FROM {{ source("lens", "lens_profiles") }} AS profiles
