select
  transaction_hash,
  donation_timestamp as event_time,
  round_id,
  round_number,
  chain_id,
  gitcoin_project_id,
  donor_address,
  amount_in_usd,
  'crowdfunding' as funding_type
from {{ ref('stg_gitcoin__donations') }}
union all
select
  null as transaction_hash,
  null as event_time,
  round_id,
  round_number,
  chain_id,
  gitcoin_project_id,
  null as donor_address,
  amount_in_usd,
  'matching_grant' as funding_type
from {{ ref('stg_gitcoin__matching') }}
