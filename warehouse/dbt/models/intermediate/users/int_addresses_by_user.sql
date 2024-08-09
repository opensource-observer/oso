with first_time_addresses as (
  select
    address,
    MIN(first_block_timestamp) as first_block_timestamp
  from {{ ref('int_first_time_addresses') }}
  group by address
),

potential_bots as (
  select distinct address
  from {{ ref('int_potential_bots') }}
),

farcaster_users as (
  select
    stg_farcaster__addresses.address,
    stg_farcaster__profiles.username as farcaster_username,
    CAST(stg_farcaster__addresses.fid as int64) as farcaster_id
  from {{ ref('stg_farcaster__addresses') }}
  inner join {{ ref('stg_farcaster__profiles') }}
    on stg_farcaster__addresses.fid = stg_farcaster__profiles.farcaster_id
  where LEFT(stg_farcaster__addresses.address, 2) = '0x'
),

lens_users as (
  select
    stg_lens__owners.profile_id as lens_id,
    stg_lens__profiles.full_name as lens_username,
    LOWER(stg_lens__owners.owned_by) as address
  from {{ ref('stg_lens__owners') }}
  inner join {{ ref('stg_lens__profiles') }}
    on stg_lens__owners.profile_id = stg_lens__profiles.lens_profile_id
)

select
  first_time_addresses.address,
  first_time_addresses.first_block_timestamp,
  farcaster_users.farcaster_id,
  farcaster_users.farcaster_username,
  lens_users.lens_id,
  lens_users.lens_username,
  COALESCE(potential_bots.address is not null, false) as potential_bot
from first_time_addresses
left join potential_bots
  on first_time_addresses.address = potential_bots.address
left join farcaster_users
  on first_time_addresses.address = farcaster_users.address
left join lens_users
  on first_time_addresses.address = lens_users.address
