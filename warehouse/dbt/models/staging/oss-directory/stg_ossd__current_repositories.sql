{{
  config(
    materialized='table'
  )
}}

{# 
  The most recent view of repositories from the ossd repositories dagster source.
#}

with ranked_repositories as (
  select
    node_id,
    id,
    url,
    name,
    name_with_owner,
    owner,
    branch,
    star_count,
    watcher_count,
    fork_count,
    is_fork,
    license_name,
    license_spdx_id,
    language,
    created_at,
    updated_at,
    ingestion_time,
    ROW_NUMBER()
      over (partition by node_id order by ingestion_time desc, id asc)
      as row_num
  from {{ oso_source('ossd', 'repositories') }}
)

select
  node_id,
  id,
  url,
  name,
  name_with_owner,
  owner,
  branch,
  star_count,
  watcher_count,
  fork_count,
  is_fork,
  license_name,
  license_spdx_id,
  language,
  created_at,
  updated_at,
  ingestion_time
from ranked_repositories
where row_num = 1
