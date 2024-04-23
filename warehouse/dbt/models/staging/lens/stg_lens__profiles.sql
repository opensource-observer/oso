{#
  Get all profile_ids mapped to the owner address and profile metadata
#}

WITH lens_owners_ordered AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY profile_id ORDER BY block_number DESC) AS rn
  FROM {{ source("lens", "lens_owners") }}
),

lens_latest_owner AS (
  SELECT
    profile_id AS profile_id,
    owned_by AS owned_by
  FROM lens_owners_ordered
  WHERE rn = 1
  ORDER BY profile_id
)

SELECT
  profiles.profile_id AS profile_id,
  profiles.name AS full_name,
  profiles.bio AS bio,
  profiles.profile_picture_snapshot_location_url AS profile_picture_url,
  profiles.cover_picture_snapshot_location_url AS cover_picture_url,
  owners.owned_by AS owner
FROM {{ source("lens", "lens_profiles") }} AS profiles
INNER JOIN lens_latest_owner AS owners
  ON profiles.profile_id = owners.profile_id
