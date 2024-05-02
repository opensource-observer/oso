{#
  This model segments developers based on monthly activity
  using the same taxonomy as in the Electric Capital
  Developer Report.

  The taxonomy is as follows:
  - Full-time developer: A developer who has made at least 10 commits
  - Part-time developer: A developer who has made less than 10 commits
  - Other contributor: A user who has not made any commits
#}

SELECT
  project_id,
  from_id,
  from_namespace AS repository_source,
  bucket_month,
  1 AS amount,
  CASE
    WHEN
      event_type = 'COMMIT_CODE' AND count_days >= 10
      THEN 'FULL_TIME_DEV'
    WHEN
      event_type = 'COMMIT_CODE' AND count_days < 10
      THEN 'PART_TIME_DEV'
    ELSE 'OTHER_CONTRIBUTOR'
  END AS user_segment_type
FROM {{ ref('int_user_events_monthly_to_project') }}
WHERE
  event_type IN (
    'COMMIT_CODE',
    'PULL_REQUEST_OPENED',
    'PULL_REQUEST_MERGED',
    'ISSUE_OPENED',
    'ISSUE_CLOSED'
  )
