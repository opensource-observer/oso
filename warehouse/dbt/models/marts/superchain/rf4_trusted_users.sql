with farcaster_users as (
  select
    fid as farcaster_id,
    address,
    CAST(
      fid < '20939'
      as int64
    ) as farcaster_prepermissionless
  from {{ ref('stg_farcaster__addresses') }}
),

eigentrust_top_users as (
  select
    1 as eigentrust_verification,
    CAST(farcaster_id as string) as farcaster_id
  from {{ ref('stg_karma3__globaltrust') }}
  where
    snapshot_time = '2024-05-21'
    and strategy_id = 1
  order by eigentrust_rank desc
  limit 42000
),

optimist_nft_holders as (
  select
    optimist_address as address,
    1 as optimist_nft_verification
  from {{ source("static_data_sources", "optimist_nft_holders") }}
),

passport_scores as (
  select
    passport_address as address,
    1 as passport_user,
    CAST(
      COALESCE(evidence_rawscore >= evidence_threshold, false) as int64
    ) as passport_verification
  from {{ ref('stg_passport__scores') }}
),

airdrop_recipients as (
  select
    address,
    1 as airdrop_recipient,
    CAST(
      COALESCE(count_drops > 1, false) as int64
    ) as airdrop_verification
  from (
    select
      LOWER(address) as address,
      COUNT(distinct airdrop_round) as count_drops
    from {{ ref('stg_optimism__airdrop_addresses') }}
    group by LOWER(address)
  )
),

all_addresses as (
  select distinct address
  from (
    select address from farcaster_users
    union all
    select address from passport_scores
    union all
    select address from optimist_nft_holders
    union all
    select address from airdrop_recipients
  )
),

trusted_user_model as (
  select
    all_addresses.address,
    CAST(farcaster_users.farcaster_id is not null as int64)
      as farcaster_user,
    COALESCE(farcaster_users.farcaster_prepermissionless, 0)
      as farcaster_prepermissionless,
    COALESCE(eigentrust_top_users.eigentrust_verification, 0)
      as eigentrust_verification,
    COALESCE(passport_scores.passport_user, 0)
      as passport_user,
    COALESCE(passport_scores.passport_verification, 0)
      as passport_verification,
    COALESCE(optimist_nft_holders.optimist_nft_verification, 0)
      as optimist_nft_verification,
    COALESCE(airdrop_recipients.airdrop_recipient, 0)
      as airdrop_recipient,
    COALESCE(airdrop_recipients.airdrop_verification, 0)
      as airdrop_verification
  from all_addresses
  left join farcaster_users
    on all_addresses.address = farcaster_users.address
  left join eigentrust_top_users
    on farcaster_users.farcaster_id = eigentrust_top_users.farcaster_id
  left join passport_scores
    on all_addresses.address = passport_scores.address
  left join optimist_nft_holders
    on all_addresses.address = optimist_nft_holders.address
  left join airdrop_recipients
    on all_addresses.address = airdrop_recipients.address
)

select
  address,
  farcaster_user,
  farcaster_prepermissionless,
  eigentrust_verification,
  passport_user,
  passport_verification,
  optimist_nft_verification,
  airdrop_recipient,
  airdrop_verification,
  (
    farcaster_user
    + farcaster_prepermissionless
    + eigentrust_verification
    + passport_verification
    + optimist_nft_verification
    + airdrop_verification
  ) > 1 as is_trusted_user
from trusted_user_model
