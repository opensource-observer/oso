{#
  This model combines the donations and matching grants data to create a single table of funding events.
  The `funding_type` column is used to differentiate between donations and matching grants.
#}


with donations as (
  select
    transaction_hash,
    donation_timestamp as event_time,
    gitcoin_round_id,
    coalesce(round_number, -1) as round_number,
    chain_id,
    gitcoin_project_id,
    project_application_title,
    project_recipient_address,
    donor_address,
    amount_in_usd,
    'DONATIONS' as funding_type
  from {{ ref('stg_gitcoin__donations') }}
),

matching as (
  select
    cast(null as string) as transaction_hash,
    funding_rounds.date_round_ended as event_time,
    matching_data.gitcoin_round_id,
    matching_data.round_number,
    matching_data.chain_id,
    matching_data.gitcoin_project_id,
    matching_data.project_application_title,
    matching_data.project_recipient_address,
    cast(null as string) as donor_address,
    matching_data.amount_in_usd,
    'MATCHING' as funding_type
  from (
    select
      gitcoin_round_id,
      coalesce(round_number, -1) as round_number,
      chain_id,
      gitcoin_project_id,
      project_application_title,
      project_recipient_address,
      amount_in_usd
    from {{ ref('stg_gitcoin__matching') }}
  ) as matching_data
  left join {{ ref('int_gitcoin_funding_rounds') }} as funding_rounds
    on
      matching_data.gitcoin_round_id = funding_rounds.gitcoin_round_id
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

events as (
  select
    {{ oso_id("'GITCOIN'", 'gitcoin_round_id', 'round_number') }}
      as funding_round_id,
    gitcoin_round_id,
    round_number,
    chain_id,
    gitcoin_project_id,
    project_application_title,
    oso_project_id,
    donor_address,
    amount_in_usd,
    funding_type,
    event_time,
    transaction_hash
  from project_directory_joined
)

select
  events.funding_round_id,
  events.gitcoin_round_id,
  events.round_number,
  funding_rounds.round_name,
  events.chain_id,
  events.gitcoin_project_id,
  events.project_application_title,
  events.oso_project_id,
  projects.project_name as oso_project_name,
  projects.display_name as oso_display_name,
  events.donor_address,
  events.amount_in_usd,
  events.funding_type,
  events.event_time,
  events.transaction_hash
from events
left join {{ ref('projects_v1') }} as projects
  on events.oso_project_id = projects.project_id
left join {{ ref('int_gitcoin_funding_rounds') }} as funding_rounds
  on events.funding_round_id = funding_rounds.funding_round_id
