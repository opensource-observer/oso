select distinct
  group_id as gitcoin_group_id,
  project_id as gitcoin_project_id,
  source as latest_gitcoin_data_source
from {{ source("gitcoin", "project_lookup") }}
