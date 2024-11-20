with start_events as (
  select
    `number`,
    actor_id as creator_id,
    to_artifact_id,
    `time` as created_at,
    `type`
  from {{ ref('int_github_pr_issue_threads') }}
  where `type` in ('PULL_REQUEST_OPENED', 'ISSUE_OPENED')
),

response_events as (
  select
    `number`,
    actor_id as responder_id,
    to_artifact_id,
    `time` as responded_at,
    `type`
  from {{ ref('int_github_pr_issue_threads') }}
  where `type` in (
    'PULL_REQUEST_MERGED',
    'PULL_REQUEST_REVIEW_COMMENT',
    'ISSUE_CLOSED',
    'ISSUE_COMMENT'
  )
),

time_to_first_response as (
  select
    start_events.number,
    start_events.to_artifact_id,
    start_events.created_at,
    'GITHUB' as event_source,
    min(resp.responded_at) as responded_at,
    cast(
      timestamp_diff(min(resp.responded_at), start_events.created_at, minute)
      as float64
    ) / 60.0 / 24.0 as time_to_first_response_days
  from start_events
  inner join response_events as resp
    on
      start_events.number = resp.number
      and start_events.to_artifact_id = resp.to_artifact_id
      and start_events.creator_id != resp.responder_id
      and (
        (
          start_events.`type` = 'ISSUE_OPENED'
          and resp.`type` in (
            'ISSUE_COMMENT', 'ISSUE_CLOSED'
          )
        )
        or
        (
          start_events.`type` = 'PULL_REQUEST_OPENED'
          and resp.`type` in (
            'PULL_REQUEST_REVIEW_COMMENT', 'PULL_REQUEST_MERGED'
          )
        )
      )
  group by
    start_events.number,
    start_events.to_artifact_id,
    start_events.created_at
),

time_to_first_response_events as (
  select
    responded_at as `time`,
    to_artifact_id,
    event_source,
    time_to_first_response_days as amount
  from time_to_first_response
)

select
  artifacts_by_project.project_id,
  time_to_first_response_events.event_source,
  time_intervals.time_interval,
  'time_to_first_response_days_average' as metric,
  avg(time_to_first_response_events.amount) as amount
from time_to_first_response_events
left join {{ ref('artifacts_by_project_v1') }} as artifacts_by_project
  on time_to_first_response_events.to_artifact_id = artifacts_by_project.artifact_id
cross join {{ ref('int_time_intervals') }} as time_intervals
where time_to_first_response_events.time >= time_intervals.start_date
group by
  artifacts_by_project.project_id,
  time_to_first_response_events.event_source,
  time_intervals.time_interval
