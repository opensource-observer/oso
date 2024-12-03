with max_dlt as (
  select max(_dlt_load_id) as max_dlt_load_id
  from {{ source("gitcoin", "all_donations") }}
)

select distinct  -- noqa: ST06
  `source` as gitcoin_data_source,
  `timestamp` as event_time,
  round_id as gitcoin_round_id,
  round_num as round_number,
  round_name,
  chain_id,
  project_id as gitcoin_project_id,
  trim(project_name) as project_application_title,
  lower(recipient_address) as project_recipient_address,
  lower(donor_address) as donor_address,
  lower(transaction_hash) as transaction_hash,
  amount_in_usd
from {{ source("gitcoin", "all_donations") }}
where
  amount_in_usd > 0
  and _dlt_load_id = (select max_dlt.max_dlt_load_id from max_dlt)
