{# 
  Contributor stats by project and event type
#}

select
  from_artifact_id as artifact_id,
  project_id,
  event_type,
  MIN(time) as first_contribution_time,
  MAX(time) as last_contribution_time,
  SUM(amount) as contribution_count
from {{ ref('int_events_to_project') }}
where
  event_type in (
    'COMMIT_CODE',
    'PULL_REQUEST_OPENED',
    'PULL_REQUEST_REOPENED',
    'PULL_REQUEST_CLOSED',
    'PULL_REQUEST_MERGED',
    'ISSUE_CLOSED',
    'ISSUE_OPENED',
    'ISSUE_REOPENED'
  )
group by
  from_artifact_id,
  project_id,
  event_type
