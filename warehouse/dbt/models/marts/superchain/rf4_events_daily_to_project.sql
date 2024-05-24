{# 
  All events to a project, bucketed by day
#}

with events as (
  select
    project_id,
    from_artifact_id,
    to_artifact_id,
    event_source,
    event_type,
    TIMESTAMP_TRUNC(time, day) as bucket_day,
    SUM(amount) as amount
  from {{ ref('int_events_to_project') }}
  where
    event_source in (
      'OPTIMISM',
      'BASE',
      'FRAX',
      'METAL',
      'MODE',
      'ZORA'
    )
    and time < '2024-05-23'
  group by
    project_id,
    from_artifact_id,
    to_artifact_id,
    event_source,
    event_type,
    TIMESTAMP_TRUNC(time, day)
)

select
  events.bucket_day,
  events.project_id,
  projects_v1.project_name,
  from_artifacts.artifact_name as from_artifact_name,
  to_artifacts.artifact_name as to_artifact_name,
  events.event_source,
  events.event_type,
  events.amount,
  case
    when rf4_trusted_users.is_trusted_user is true
      then rf4_trusted_users.address
  end as trusted_user_id
from events
left join {{ ref('artifacts_v1') }} as to_artifacts
  on events.to_artifact_id = to_artifacts.artifact_id
left join {{ ref('artifacts_v1') }} as from_artifacts
  on events.from_artifact_id = from_artifacts.artifact_id
left join {{ ref('projects_v1') }}
  on events.project_id = projects_v1.project_id
left join {{ ref('rf4_trusted_users') }}
  on from_artifacts.artifact_name = rf4_trusted_users.address
where
  to_artifacts.artifact_type = 'CONTRACT'
