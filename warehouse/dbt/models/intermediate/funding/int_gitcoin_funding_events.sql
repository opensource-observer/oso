{#
  This model combines the donations and matching grants data to create a single table of funding events.
  The `funding_type` column is used to differentiate between donations and matching grants.
#}


with donations as (
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
),

matching as (
  select
    null as transaction_hash,
    funding_rounds.date_round_ended as event_time,
    round_id,
    round_number,
    chain_id, 
    gitcoin_project_id,
    null as donor_address,
    amount_in_usd,
    'MATCHING' as funding_type
  from (
    select
      round_id,
      coalesce(round_number, -1) as round_number,
      chain_id,
      gitcoin_project_id,
      amount_in_usd
    from {{ ref('stg_gitcoin__matching') }}
  ) as matching_data
  left join {{ ref('int_gitcoin_funding_rounds') }} as funding_rounds
    on
      matching_data.round_id = funding_rounds.round_id
      and matching_data.round_number = funding_rounds.round_number
),

unioned_events as (
  select * from donations
  union all
  select * from matching
),

project_directory_joined as (
  select
    unioned_events.*,
    project_directory.oso_project_id
  from unioned_events
  left join {{ ref('int_gitcoin_project_directory') }} as project_directory
    on unioned_events.gitcoin_project_id = project_directory.gitcoin_project_id
  where amount_in_usd > 0
),

final as (
  select
    {{ oso_id("'GITCOIN'", 'round_id', 'round_number') }}
      as funding_round_id,
    round_id,
    round_number,
    chain_id,
    gitcoin_project_id,
    oso_project_id,
    donor_address,
    amount_in_usd,
    funding_type,
    event_time,
    transaction_hash
  from project_directory_joined
)

select
  funding_round_id,
  round_id,
  round_number,
  chain_id,
  gitcoin_project_id,
  oso_project_id,
  projects.project_name as oso_project_name,
  donor_address,
  amount_in_usd,
  funding_type,
  event_time,
  transaction_hash
from final
left join {{ ref('projects_v') }} as projects
  on final.oso_project_id = projects.project_id
