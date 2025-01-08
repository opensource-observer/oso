select
  event_time,
  gitcoin_data_source,
  gitcoin_round_id,
  round_number,
  round_type,
  main_round_label,
  round_name,
  oso_generated_round_label,
  gitcoin_project_id,
  project_application_title,
  oso_project_id,
  oso_project_name,
  oso_display_name,
  donor_address,
  amount_in_usd
from {{ ref('int_gitcoin_funding_events') }}
