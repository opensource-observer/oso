{# 
  All events to a project, bucketed by day
#}

with events as (
  select
    project_id,
    from_artifact_id,
    from_artifact_name,
    to_artifact_id,
    to_artifact_name,
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
    from_artifact_name,
    to_artifact_id,
    to_artifact_name,
    event_source,
    event_type,
    TIMESTAMP_TRUNC(time, day)
)

select
  bucket_day,
  project_id,
  from_artifact_id,
  from_artifact_name,
  to_artifact_id,
  to_artifact_name,
  event_source,
  event_type,
  amount,
  (
    from_artifact_name in (
      select artifact_name
      from {{ ref('rf4_trusted_users') }}
    )
  ) as is_from_trusted_user
from events
