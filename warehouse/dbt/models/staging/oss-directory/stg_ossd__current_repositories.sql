{# 
  The most recent view of repositories from the github-resolve-repos cloudquery plugin.
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
    ingestion_time,
    ROW_NUMBER()
      over (partition by node_id order by ingestion_time desc, id asc)
      as row_num
  from {{ oso_source('ossd', 'repositories') }}
)

select *
from ranked_repositories
where row_num = 1
