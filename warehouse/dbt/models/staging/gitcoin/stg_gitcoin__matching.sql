with max_dlt as (
  select max(_dlt_load_id) as max_dlt_load_id
  from {{ source("gitcoin", "all_matching") }}
)

select distinct  -- noqa: ST06
  'MatchFunding' as gitcoin_data_source,
  `timestamp` as event_time,
  round_id as gitcoin_round_id,
  round_num as round_number,
  cast(null as string) as round_name,
  chain_id,
  project_id as gitcoin_project_id,
  trim(title) as project_application_title,
  lower(recipient_address) as project_recipient_address,
  cast(null as string) as donor_address,
  cast(null as string) as transaction_hash,
  match_amount_in_usd as amount_in_usd
from {{ source("gitcoin", "all_matching") }}
where
  match_amount_in_usd > 0
  and _dlt_load_id = (select max_dlt.max_dlt_load_id from max_dlt)
