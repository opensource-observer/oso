{#
  This model combines the donations and matching grants data to create a single table of funding events.
  The `funding_type` column is used to differentiate between donations and matching grants.
  The `event_time` data has some issues. It is missing for matching grants, so we use the most recent donation timestamp as a placeholder. To the cGrants data, we use a placeholder date of 2023-07-01.
#}


with last_donation_by_round as (
  select
    round_id,
    round_number,
    gitcoin_project_id,
    max(donation_timestamp) as assumed_event_time
  from {{ ref('stg_gitcoin__donations') }}
  group by
    round_id,
    round_number,
    gitcoin_project_id
),

unioned_events as (
  select
    transaction_hash,
    donation_timestamp as event_time,
    round_id,
    round_number,
    chain_id,
    gitcoin_project_id,
    donor_address,
    amount_in_usd,
    'DONATIONS' as funding_type
  from {{ ref('stg_gitcoin__donations') }}

  union all

  select
    null as transaction_hash,
    last_donation_by_round.assumed_event_time as event_time,
    matching.round_id,
    matching.round_number,
    matching.chain_id,
    matching.gitcoin_project_id,
    null as donor_address,
    matching.amount_in_usd,
    'MATCHING' as funding_type
  from {{ ref('stg_gitcoin__matching') }} as matching
  left join last_donation_by_round
    on
      matching.round_id = last_donation_by_round.round_id
      and matching.round_number = last_donation_by_round.round_number
      and matching.gitcoin_project_id = last_donation_by_round.gitcoin_project_id
)

select
  transaction_hash,
  round_id,
  round_number,
  chain_id,
  gitcoin_project_id,
  donor_address,
  amount_in_usd,
  funding_type,
  coalesce(event_time, timestamp('2023-07-01')) as event_time
from unioned_events
where amount_in_usd > 0
