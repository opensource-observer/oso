{# 
  The most recent view of repositories from the github-resolve-repos cloudquery plugin.
#}
with most_recent_sync as (
  select MAX(ingestion_time) as ingestion_time
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
  repositories.language,
  repositories.ingestion_time
from {{ oso_source('ossd', 'repositories') }} as repositories
where repositories.ingestion_time = (select * from most_recent_sync)
