MODEL (
  name metrics.stg_farcaster__profiles,
  description 'Get all farcaster profiles from the JSON',
  dialect trino,
  kind FULL,
);

select
  @oso_id('oso', fid) as user_id,
  cast(profiles.fid as string) as farcaster_id,
  profiles.custody_address as custody_address,
  json_extract_scalar(profiles.data, '$.username') as username,
  json_extract_scalar(profiles.data, '$.display') as display_name,
  json_extract_scalar(profiles.data, '$.pfp') as profile_picture_url,
  json_extract_scalar(profiles.data, '$.bio') as bio,
  json_extract_scalar(profiles.data, '$.url') as url
from @oso_source('bigquery.farcaster.profiles') as profiles
