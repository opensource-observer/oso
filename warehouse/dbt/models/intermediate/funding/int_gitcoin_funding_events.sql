with unioned_funding_events as (
  select * from {{ ref('stg_gitcoin__donations') }}
  union all
  select * from {{ ref('stg_gitcoin__matching') }}
),

labeled_funding_events as (
  select
    *,
    case
      when (
        gitcoin_data_source in ('MatchFunding', 'CGrants')
        and round_number between 1 and 15
      ) then concat('GG-', lpad(cast(round_number as string), 2, '0'))
      when (
        gitcoin_data_source in ('MatchFunding', 'Alpha')
        and round_number = 16
      ) then 'GG-16'
      when (
        gitcoin_data_source in ('MatchFunding', 'GrantsStack')
        and round_number is not null
      ) then concat('GG-', lpad(cast(round_number as string), 2, '0'))
    end as main_round_label,
    case
      when (
        gitcoin_data_source = 'CGrants'
        and round_number is null
      ) then 'DirectDonations'
      when (
        gitcoin_data_source in ('MatchFunding', 'GrantsStack')
        and round_number is null
      ) then 'PartnerRound'
      else 'MainRound'
    end as round_type
  from unioned_funding_events
),

joined_events as (
  select
    labeled_funding_events.*,
    directory.oso_project_id,
    projects.project_name as oso_project_name,
    projects.display_name as oso_display_name
  from labeled_funding_events
  left join {{ ref('int_gitcoin_project_directory') }} as directory
    on labeled_funding_events.gitcoin_project_id = directory.gitcoin_project_id
  left join {{ ref('projects_v1') }} as projects
    on directory.oso_project_id = projects.project_id
  where amount_in_usd > 0
)

select
  event_time,
  gitcoin_data_source,
  gitcoin_round_id,
  round_number,
  round_type,
  main_round_label,
  round_name,
  chain_id,
  gitcoin_project_id,
  project_application_title,
  oso_project_id,
  oso_project_name,
  oso_display_name,
  donor_address,
  amount_in_usd,
  transaction_hash
from joined_events
