MODEL (
  name oso.stg_lens__profiles,
  description 'Get all profile_ids mapped to the owner address and profile metadata',
  dialect trino,
  kind FULL
);

SELECT
  @oso_id('oso', profile_id) AS user_id,
  profiles.profile_id AS lens_profile_id,
  profiles.name AS full_name,
  profiles.bio AS bio,
  profiles.profile_picture_snapshot_location_url AS profile_picture_url,
  profiles.cover_picture_snapshot_location_url AS cover_picture_url
FROM @oso_source('bigquery.lens_v2_polygon.profile_metadata') AS profiles