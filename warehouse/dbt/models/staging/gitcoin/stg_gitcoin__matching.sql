select distinct
  round_id as round_id,
  round_num as round_number,
  chain_id,
  project_id as gitcoin_project_id,
  match_amount_in_usd as amount_in_usd,
  TRIM(title) as round_title,
  LOWER(recipient_address) as project_recipient_address
from {{ source("gitcoin", "all_matching") }}
where match_amount_in_usd > 0
