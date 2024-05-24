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
  {# draft model for testing #}
  select
    1 as eigentrust_verification,
    CAST(farcaster_id as string) as farcaster_id
  from {{ ref('stg_karma3__globaltrust') }}
  where
    snapshot_time = '2024-05-21'
    and strategy_id = 1
  order by eigentrust_rank desc
  limit 50000
),

web_of_trust as (
  {# draft model for testing #}
  select
    1 as vitalik_verification,
    CAST(fof_id as string) as farcaster_id
  from (
    select
      l2.peer_farcaster_id as fof_id,
      COUNT(distinct l1.peer_farcaster_id) as edge_count
    from {{ ref('stg_karma3__localtrust') }} as l1
    left join {{ ref('stg_karma3__localtrust') }} as l2
      on l1.peer_farcaster_id = l2.farcaster_id
    where
      l1.farcaster_id = 5650
      and l1.strategy_id = 1
      and l2.strategy_id = 1
    group by l2.peer_farcaster_id
  )
  where edge_count > 1
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

all_addresses as (
  select distinct address
  from (
    select address from farcaster_users
    union all
    select address from passport_scores
    union all
    select address from optimist_nft_holders
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
    COALESCE(web_of_trust.vitalik_verification, 0)
      as vitalik_verification,
    COALESCE(passport_scores.passport_user, 0)
      as passport_user,
    COALESCE(passport_scores.passport_verification, 0)
      as passport_verification,
    COALESCE(optimist_nft_holders.optimist_nft_verification, 0)
      as optimist_nft_verification
  from all_addresses
  left join farcaster_users
    on all_addresses.address = farcaster_users.address
  left join eigentrust_top_users
    on farcaster_users.farcaster_id = eigentrust_top_users.farcaster_id
  left join web_of_trust
    on farcaster_users.farcaster_id = web_of_trust.farcaster_id
  left join passport_scores
    on all_addresses.address = passport_scores.address
  left join optimist_nft_holders
    on all_addresses.address = optimist_nft_holders.address
)

select
  address,
  farcaster_user,
  farcaster_prepermissionless,
  eigentrust_verification,
  vitalik_verification,
  passport_user,
  passport_verification,
  optimist_nft_verification,
  case
    when (
      farcaster_prepermissionless
      + eigentrust_verification
      + vitalik_verification
    ) > 0
      then true
    when (
      farcaster_user = 1
      and (
        passport_verification
        + optimist_nft_verification
      ) > 0
    ) then true
    else false
  end
    as is_trusted_user
from trusted_user_model
