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
    and time < '2024-06-01'
  group by
    project_id,
    from_artifact_id,
    to_artifact_id,
    event_source,
    event_type,
    TIMESTAMP_TRUNC(time, day)
),

artifacts as (
  select distinct
    artifact_id,
    artifact_name
  from {{ ref('artifacts_v1') }}
),

{# use snapshot instead of live model as farcaster addresses may change #}
rf4_trusted_users as (
  select
    address,
    true as is_trusted_user
  from {{ source('static_data_sources', 'op_rf4_trusted_addresses') }}
),

events_to_project as (
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
  left join artifacts as to_artifacts
    on events.to_artifact_id = to_artifacts.artifact_id
  left join artifacts as from_artifacts
    on events.from_artifact_id = from_artifacts.artifact_id
  left join {{ ref('projects_v1') }}
    on events.project_id = projects_v1.project_id
  left join rf4_trusted_users
    on from_artifacts.artifact_name = rf4_trusted_users.address
  where events.amount > 0
),

duped_contracts as (
  select distinct
    event_source,
    to_artifact_name,
    project_name
  from events_to_project
  where project_name in ('zora', 'aerodrome-finance')
),

filtered_events as (
  select events_to_project.*
  from events_to_project
  left join duped_contracts
    on
      events_to_project.to_artifact_name = duped_contracts.to_artifact_name
      and events_to_project.event_source = duped_contracts.event_source
  where
    duped_contracts.project_name is null
    or duped_contracts.project_name = events_to_project.project_name
)

select
  bucket_day,
  project_id,
  project_name,
  from_artifact_name,
  to_artifact_name,
  event_source,
  event_type,
  amount,
  trusted_user_id
from filtered_events
