with max_dlt as (
  select max(_dlt_load_id) as max_dlt_load_id
  from {{ source("gitcoin", "all_matching") }}
)

select distinct
  round_id as gitcoin_round_id,
  round_num as round_number,
  chain_id,
  project_id as gitcoin_project_id,
  match_amount_in_usd as amount_in_usd,
  `timestamp`,
  trim(title) as project_application_title,
  lower(recipient_address) as project_recipient_address
from {{ source("gitcoin", "all_matching") }}
where
  match_amount_in_usd > 0
  and _dlt_load_id = (select max_dlt.max_dlt_load_id from max_dlt)
