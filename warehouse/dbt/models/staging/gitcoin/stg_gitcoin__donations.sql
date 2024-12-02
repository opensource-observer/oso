select distinct
  `source` as gitcoin_data_source,
  `timestamp` as donation_timestamp,
  round_id,
  round_num as round_number,
  round_name,
  chain_id,
  project_id as gitcoin_project_id,
  amount_in_usd,
  LOWER(recipient_address) as project_recipient_address,
  LOWER(donor_address) as donor_address,
  LOWER(transaction_hash) as transaction_hash,
  TRIM(project_name) as project_application_title
from {{ source("gitcoin", "all_donations") }}
where amount_in_usd > 0
