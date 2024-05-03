{# 
  Developer stats by project and repo source
#}

select
  from_id,
  from_namespace as repository_source,
  project_id,
  MIN(bucket_day) as date_first_contribution,
  MAX(bucket_day) as date_last_contribution,
  SUM(amount) as count_events
from {{ ref('int_user_events_daily_to_project') }}
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
group by 1, 2, 3
