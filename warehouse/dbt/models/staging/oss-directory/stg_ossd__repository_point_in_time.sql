{#
Point in time view for repository data.
#}
select
  repo.ingestion_time as `time`,
  "GITHUB" as artifact_source,
  "REPOSITORY" as artifact_type,
  repo.owner as artifact_namespace,
  repo.name as artifact_name,
  repo.id as artifact_source_id,
  unpivoted.metric as metric,
  unpivoted.amount as amount
from {{ oso_source('ossd', 'repositories') }} as repo, unnest([
  struct("fork_count" as metric, fork_count as amount),
  struct("star_count" as metric, star_count as amount),
  struct("watcher_count" as metric, watcher_count as amount)
]) as unpivoted
