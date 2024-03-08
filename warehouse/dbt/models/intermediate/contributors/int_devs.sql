SELECT
  e.project_id,
  e.to_namespace AS repository_source,
  e.from_id,
  1 AS amount,
  TIMESTAMP_TRUNC(e.time, MONTH) AS bucket_month,
  CASE
    WHEN
      COUNT(DISTINCT CASE WHEN e.event_type = 'COMMIT_CODE' THEN e.time END)
      >= 10
      THEN 'FULL_TIME_DEV'
    WHEN
      COUNT(DISTINCT CASE WHEN e.event_type = 'COMMIT_CODE' THEN e.time END)
      >= 1
      THEN 'PART_TIME_DEV'
    ELSE 'OTHER_CONTRIBUTOR'
  END AS user_segment_type
FROM {{ ref('int_events_to_project') }} AS e
WHERE
  e.event_type IN (
    'PULL_REQUEST_CREATED',
    'PULL_REQUEST_MERGED',
    'COMMIT_CODE',
    'ISSUE_CLOSED',
    'ISSUE_CREATED'
  )
GROUP BY e.project_id, bucket_month, e.from_id, repository_source
