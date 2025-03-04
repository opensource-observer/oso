model(
    name oso.stg_lens__profiles,
    description 'Get all profile_ids mapped to the owner address and profile metadata',
    dialect trino,
    kind full,
)
;

select
    @oso_id('oso', profile_id) as user_id,
    profiles.profile_id as lens_profile_id,
    profiles.name as full_name,
    profiles.bio as bio,
    profiles.profile_picture_snapshot_location_url as profile_picture_url,
    profiles.cover_picture_snapshot_location_url as cover_picture_url
from @oso_source('bigquery.lens_v2_polygon.profile_metadata') as profiles
