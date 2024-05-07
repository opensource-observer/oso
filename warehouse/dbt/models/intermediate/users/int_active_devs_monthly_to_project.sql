{#
  This model segments developers based on monthly activity
  using the same taxonomy as in the Electric Capital
  Developer Report.

  The taxonomy is as follows:
  - Full-time developer: A developer who has made at least 10 commits
  - Part-time developer: A developer who has made less than 10 commits
  - Other contributor: A user who has not made any commits
#}

select
  project_id,
  from_artifact_id,
  bucket_month,
  1 as amount,
  case
    when
      event_type = 'COMMIT_CODE' and count_days >= 10
      then 'FULL_TIME_DEV'
    when
      event_type = 'COMMIT_CODE' and count_days < 10
      then 'PART_TIME_DEV'
    else 'OTHER_CONTRIBUTOR'
  end as user_segment_type
from {{ ref('int_user_events_monthly_to_project') }}
where
  event_type in (
    'COMMIT_CODE',
    'PULL_REQUEST_OPENED',
    'PULL_REQUEST_MERGED',
    'ISSUE_OPENED',
    'ISSUE_CLOSED'
  )
