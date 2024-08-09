with optimist_nft_holders as (
  select LOWER(optimist_address) as address
  from {{ source("static_data_sources", "optimist_nft_holders") }}
),

airdrop_recipients as (
  select
    LOWER(address) as address,
    COUNT(distinct airdrop_round) as num_airdrops
  from {{ ref('stg_optimism__airdrop_addresses') }}
  group by LOWER(address)
),

user_model as (
  select
    addresses.address,
    artifacts_by_address.artifact_id,
    COALESCE(optimist_nft_holders.address is not null, false)
      as is_optimist_nft_holder,
    COALESCE(airdrop_recipients.num_airdrops, 0) as num_optimism_airdrops,
    COALESCE(addresses.potential_bot, false) as is_potential_bot,
    COALESCE(addresses.farcaster_username is not null, false)
      as is_farcaster_user,
    COALESCE(addresses.farcaster_id < 20939, false)
      as is_farcaster_prepermissionless
  from {{ ref('int_addresses_by_user') }} as addresses
  left join optimist_nft_holders
    on addresses.address = optimist_nft_holders.address
  left join airdrop_recipients
    on addresses.address = airdrop_recipients.address
  left join {{ ref('int_artifacts_by_address') }} as artifacts_by_address
    on addresses.address = artifacts_by_address.artifact_name
)

select
  address,
  artifact_id,
  num_optimism_airdrops,
  is_optimist_nft_holder,
  is_potential_bot,
  is_farcaster_user,
  is_farcaster_prepermissionless,
  (
    not is_potential_bot and (
      is_farcaster_user and (
        num_optimism_airdrops > 1
        or is_farcaster_prepermissionless
        or is_optimist_nft_holder
      )
      or (
        num_optimism_airdrops > 1
        and is_optimist_nft_holder
      )
    )
  ) as is_trusted_user
from user_model
