select
  oso_generated_round_label,
  round_type,
  main_round_label,
  count_projects,
  unique_donors,
  match_funding_amount_in_usd,
  total_funding_amount_in_usd,
  first_event_time,
  last_event_time
from {{ ref('int_gitcoin_funding_rounds') }}
