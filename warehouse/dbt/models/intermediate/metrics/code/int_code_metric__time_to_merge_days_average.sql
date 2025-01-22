with pr_events as (
  select
    `number`,
    to_artifact_id,
    `time` as created_at
  from {{ ref('int_github_pr_issue_threads') }}
  where `type` = 'PULL_REQUEST_OPENED'
),

merge_events as (
  select
    `number`,
    to_artifact_id,
    `time` as merged_at
  from {{ ref('int_github_pr_issue_threads') }}
  where `type` = 'PULL_REQUEST_MERGED'
),

time_to_merge as (
  select
    pr.number,
    pr.to_artifact_id,
    pr.created_at,
    m.merged_at,
    'GITHUB' as event_source,
    CAST(
      TIMESTAMP_DIFF(m.merged_at, pr.created_at, minute)
      as FLOAT64
    ) / 60.0 / 24.0 as time_to_merge_days
  from pr_events as pr
  inner join merge_events as m
    on
      pr.number = m.number
      and pr.to_artifact_id = m.to_artifact_id
  where m.merged_at > pr.created_at
),

time_to_merge_events as (
  select
    merged_at as `time`,
    to_artifact_id,
    event_source,
    time_to_merge_days as amount
  from time_to_merge
)

select
  artifacts_by_project.project_id,
  time_to_merge_events.event_source,
  time_intervals.time_interval,
  'time_to_merge_days_average' as metric,
  AVG(time_to_merge_events.amount) as amount
from time_to_merge_events
left join {{ ref('artifacts_by_project_v1') }} as artifacts_by_project
  on time_to_merge_events.to_artifact_id = artifacts_by_project.artifact_id
cross join {{ ref('int_time_intervals') }} as time_intervals
where time_to_merge_events.time >= time_intervals.start_date
group by
  artifacts_by_project.project_id,
  time_to_merge_events.event_source,
  time_intervals.time_interval
