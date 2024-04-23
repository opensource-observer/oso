{#
  This model aggregates user events to project level on
  a daily basis. It is used to calculate various 
  user engagement metrics by project.
#}

SELECT
  from_id,
  from_namespace,
  project_id,
  event_type,
  TIMESTAMP_TRUNC(time, DAY) AS bucket_day,
  SUM(amount) AS amount
FROM {{ ref('int_events_to_project') }}
WHERE
  event_type IN (
    'COMMIT_CODE',
    'PULL_REQUEST_OPENED',
    'PULL_REQUEST_REOPENED',
    'PULL_REQUEST_CLOSED',
    'PULL_REQUEST_MERGED',
    'ISSUE_CLOSED',
    'ISSUE_OPENED',
    'ISSUE_REOPENED',
    'CONTRACT_INVOCATION_DAILY_COUNT'
  )
GROUP BY
  from_id,
  from_namespace,
  project_id,
  event_type,
  TIMESTAMP_TRUNC(time, DAY)
