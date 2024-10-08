with max_dlt as (
  select max(_dlt_load_id) as max_dlt_load_id
  from {{ source("gitcoin", "project_lookup") }}
)

select distinct
  group_id as gitcoin_group_id,
  project_id as gitcoin_project_id,
  source as latest_gitcoin_data_source
from {{ source("gitcoin", "project_lookup") }}
where _dlt_load_id = (select max_dlt.max_dlt_load_id from max_dlt)
