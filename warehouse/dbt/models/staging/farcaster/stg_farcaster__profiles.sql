{{ 
  config(
    materialized='table'
  )
}}

{#
  Get all farcaster profiles from the JSON
#}

select
  {{ oso_id('"oso"', 'fid') }} as user_id,
  cast(profiles.fid as string) as farcaster_id,
  profiles.custody_address as custody_address,
  json_value(profiles.data, "$.username") as username,
  json_value(profiles.data, "$.display") as display_name,
  json_value(profiles.data, "$.pfp") as profile_picture_url,
  json_value(profiles.data, "$.bio") as bio,
  json_value(profiles.data, "$.url") as url
from {{ source("farcaster", "farcaster_profiles") }} as profiles
