with max_dlt as (
  select max(_dlt_load_id) as max_dlt_load_id
  from {{ source("gitcoin", "project_groups_summary") }}
)

select
  group_id as gitcoin_group_id,
  latest_created_project_id as latest_gitcoin_project_id,
  total_amount_donated as total_amount_donated_in_usd,
  application_count as group_application_count,
  latest_created_application as latest_project_application_timestamp,
  latest_source as latest_gitcoin_data_source,
  trim(title) as project_application_title,
  lower(latest_payout_address) as latest_project_recipient_address,
  trim(lower(latest_website)) as latest_project_website,
  trim(lower(latest_project_twitter)) as latest_project_twitter,
  trim(lower(latest_project_github)) as latest_project_github
from {{ source("gitcoin", "project_groups_summary") }}
where _dlt_load_id = (select max_dlt.max_dlt_load_id from max_dlt)
