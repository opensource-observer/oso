{#
  This model segments developers based on monthly activity
  using the same taxonomy as in the Electric Capital
  Developer Report.

  The taxonomy is as follows:
  - Full-time developer: A developer who has made at least 10 commits
  - Part-time developer: A developer who has made less than 10 commits
  - Other contributor: A user who has not made any commits
#}

with activity as (
  select
    project_id,
    from_artifact_id,
    event_type,
    bucket_day,
    TIMESTAMP_TRUNC(bucket_day, month) as bucket_month
  from {{ ref('int_events_daily_to_project') }}
  where
    event_type in (
      'COMMIT_CODE',
      'PULL_REQUEST_OPENED',
      'PULL_REQUEST_REOPENED',
      'PULL_REQUEST_MERGED',
      'PULL_REQUEST_CLOSED',
      'ISSUE_OPENED',
      'ISSUE_REOPENED',
      'ISSUE_CLOSED'
    )
),

user_activity as (
  select
    project_id,
    from_artifact_id,
    bucket_month,
    SUM(
      case when event_type = 'COMMIT_CODE' then 1 else 0 end
    ) as commit_days,
    SUM(
      case when event_type != 'COMMIT_CODE' then 1 else 0 end
    ) as other_contrib_days
  from activity
  group by
    project_id,
    from_artifact_id,
    bucket_month
)

select
  project_id,
  from_artifact_id,
  bucket_month,
  case
    when commit_days >= 10 then 'FULL_TIME_DEVELOPER'
    when commit_days between 1 and 9 then 'PART_TIME_DEVELOPER'
    when other_contrib_days >= 10 then 'FULL_TIME_CONTRIBUTOR'
    else 'PART_TIME_CONTRIBUTOR'
  end as user_segment_type
from user_activity
