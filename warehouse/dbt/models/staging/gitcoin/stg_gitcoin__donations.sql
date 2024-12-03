with max_dlt as (
  select max(_dlt_load_id) as max_dlt_load_id
  from {{ source("gitcoin", "all_donations") }}
)

select distinct
  `source` as gitcoin_data_source,
  `timestamp` as donation_timestamp,
  round_id as gitcoin_round_id,
  round_num as round_number,
  round_name,
  chain_id,
  project_id as gitcoin_project_id,
  amount_in_usd,
  lower(recipient_address) as project_recipient_address,
  lower(donor_address) as donor_address,
  lower(transaction_hash) as transaction_hash,
  trim(project_name) as project_application_title
from {{ source("gitcoin", "all_donations") }}
where
  amount_in_usd > 0
  and _dlt_load_id = (select max_dlt.max_dlt_load_id from max_dlt)
