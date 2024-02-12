SELECT
  e.project_slug,
  e.from_source_id,
  e.from_namespace,
  e.from_type,
  TIMESTAMP_TRUNC(e.time, MONTH) AS bucket_month,
  CASE 
    WHEN COUNT(DISTINCT CASE WHEN e.type = 'COMMIT_CODE' THEN e.time END) >= 10 THEN 'FULL_TIME_DEV'
    WHEN COUNT(DISTINCT CASE WHEN e.type = 'COMMIT_CODE' THEN e.time END) >= 1 THEN 'PART_TIME_DEV'
    ELSE 'OTHER_CONTRIBUTOR'
  END AS segment_type,
  1 AS amount
FROM {{ ref('all_events_to_project') }} as e
WHERE 
  e.type IN (
    'PULL_REQUEST_CREATED',
    'PULL_REQUEST_MERGED',
    'COMMIT_CODE',
    'ISSUE_CLOSED',
    'ISSUE_CREATED'
  )
GROUP BY
  project_slug,
  from_source_id,
  from_namespace,
  from_type,
  bucket_month