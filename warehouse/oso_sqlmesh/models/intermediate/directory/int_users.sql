MODEL (
  name metrics.int_users,
  description 'All users',
  kind FULL,
);

with farcaster_users as (
  select
    user_id,
    farcaster_id as user_source_id,
    'FARCASTER' as user_source,
    display_name,
    profile_picture_url,
    bio,
    url
  from metrics.stg_farcaster__profiles
),

lens_users as (
  select
    user_id,
    lens_profile_id as user_source_id,
    'LENS' as user_source,
    full_name as display_name,
    profile_picture_url,
    bio,
    '' as url
  from metrics.stg_lens__profiles
),

github_users as (
  select
    from_artifact_id as user_id,
    from_artifact_source_id as user_source_id,
    'GITHUB' as user_source,
    display_name,
    '' as profile_picture_url,
    '' as bio,
    'https://github.com/' || display_name as url
  from (
    select
      from_artifact_id,
      from_artifact_source_id,
      MAX_BY(LOWER(from_artifact_name), time) as display_name
    from metrics.int_events__github
    group by from_artifact_id, from_artifact_source_id
  )
)

select * from farcaster_users
union all
select * from lens_users
union all
select * from github_users
