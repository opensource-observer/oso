MODEL (
  name metrics.int_artifacts_history,
  description 'Currently this only captures the history of git_users. It does not capture git_repo naming histories.',
  kind FULL,
);

with user_events as (
  {# `from` actor artifacts derived from all events #}
  select
    event_source as artifact_source,
    from_artifact_source_id as artifact_source_id,
    from_artifact_type as artifact_type,
    from_artifact_namespace as artifact_namespace,
    from_artifact_name as artifact_name,
    '' as artifact_url,
    time
  from metrics.int_events
)

select
  LOWER(artifact_source_id) as artifact_source_id,
  UPPER(artifact_source) as artifact_source,
  UPPER(artifact_type) as artifact_type,
  LOWER(artifact_namespace) as artifact_namespace,
  LOWER(artifact_url) as artifact_url,
  LOWER(artifact_name) as artifact_name,
  MAX(time) as last_used,
  MIN(time) as first_used
from user_events
group by
  artifact_source_id,
  artifact_source,
  artifact_type,
  artifact_namespace,
  artifact_url,
  artifact_name
