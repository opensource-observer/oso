MODEL (
  name oso.stg_farcaster__profiles,
  description 'Get all farcaster profiles from the JSON',
  dialect trino,
  kind FULL,
  audit (trino_parquets_not_missing) 
);

SELECT
  @oso_entity_id('FARCASTER', '', fid) AS user_id,
  profiles.fid::VARCHAR AS farcaster_id,
  profiles.custody_address AS custody_address,
  JSON_EXTRACT_SCALAR(profiles.data, '$.username') AS username,
  JSON_EXTRACT_SCALAR(profiles.data, '$.display') AS display_name,
  JSON_EXTRACT_SCALAR(profiles.data, '$.pfp') AS profile_picture_url,
  JSON_EXTRACT_SCALAR(profiles.data, '$.bio') AS bio,
  JSON_EXTRACT_SCALAR(profiles.data, '$.url') AS url
FROM @oso_source('bigquery.farcaster.profiles') AS profiles
