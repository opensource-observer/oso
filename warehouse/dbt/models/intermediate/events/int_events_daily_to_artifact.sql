{# 
  All events to an artifact, bucketed by day
  As some artifacts may be associated with multiple projects,
  we need to select distinct first and then do the grouping
#}

with events as (
  select distinct
    from_artifact_id,
    to_artifact_id,
    event_source,
    event_type,
    time,
    amount
  from {{ ref('int_events') }}
)

select
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(time, day) as bucket_day,
  SUM(amount) as amount
from events
group by
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(time, day)
