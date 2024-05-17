{# 
  The most recent view of repositories from the github-resolve-repos cloudquery plugin.
#}
with most_recent_sync as (
  select MAX(_cq_sync_time) as sync_time
  from {{ oso_source('ossd', 'repositories') }}
)

select
  repositories.node_id,
  repositories.id,
  repositories.url,
  repositories.name,
  repositories.name_with_owner,
  repositories.owner,
  repositories.branch,
  repositories.star_count,
  repositories.watcher_count,
  repositories.fork_count,
  repositories.is_fork,
  repositories.license_name,
  repositories.license_spdx_id,
  repositories._cq_sync_time as `sync_time`
from {{ oso_source('ossd', 'repositories') }} as repositories
where _cq_sync_time = (select * from most_recent_sync)
