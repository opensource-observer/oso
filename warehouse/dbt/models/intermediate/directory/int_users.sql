with farcaster_users as (
  select
    user_id,
    farcaster_id as user_source_id,
    "FARCASTER" as user_source,
    display_name,
    profile_picture_url,
    bio,
    url
  from {{ ref('stg_farcaster__profiles') }}
),

lens_users as (
  select
    user_id,
    lens_profile_id as user_source_id,
    "LENS" as user_source,
    full_name as display_name,
    profile_picture_url,
    bio,
    "" as url
  from {{ ref('stg_lens__profiles') }}
)

select * from farcaster_users
union all
select * from lens_users
