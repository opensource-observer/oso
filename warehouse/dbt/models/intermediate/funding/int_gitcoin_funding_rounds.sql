select
  oso_generated_round_label,
  round_type,
  main_round_label,
  min(event_time) as first_event_time,
  max(event_time) as last_event_time,
  count(distinct gitcoin_project_id) as count_projects,
  count(distinct donor_address) as unique_donors,
  sum(
    case
      when gitcoin_data_source = 'MatchFunding' then amount_in_usd
      else 0
    end
  ) as match_funding_amount_in_usd,
  sum(amount_in_usd) as total_funding_amount_in_usd
from {{ ref('int_gitcoin_funding_events') }}
group by
  oso_generated_round_label,
  round_type,
  main_round_label
order by oso_generated_round_label
