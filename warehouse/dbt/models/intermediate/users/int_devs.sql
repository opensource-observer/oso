{# 
  Developer stats by project and repo source
#}

SELECT
  from_id,
  from_namespace AS repository_source,
  project_id,
  MIN(bucket_day) AS date_first_contribution,
  MAX(bucket_day) AS date_last_contribution,
  SUM(amount) AS count_events
FROM {{ ref('int_user_events_daily_to_project') }}
WHERE
  event_type IN (
    'COMMIT_CODE',
    'PULL_REQUEST_OPENED',
    'PULL_REQUEST_REOPENED',
    'PULL_REQUEST_CLOSED',
    'PULL_REQUEST_MERGED',
    'ISSUE_CLOSED',
    'ISSUE_OPENED',
    'ISSUE_REOPENED'
  )
GROUP BY 1, 2, 3
