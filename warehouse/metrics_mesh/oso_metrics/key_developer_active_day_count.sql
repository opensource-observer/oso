select distinct
  now() as metrics_sample_date,
  events.event_source,
  events.to_artifact_id as to_artifact_id,
  events.from_artifact_id as from_artifact_id,
  'DEVELOPER_ACTIVE_DAYS' as metric,
  count(distinct events.bucket_day) as amount,
  'COUNT' as unit
from metrics.events_daily_to_artifact as events
where event_type in (
  'COMMIT_CODE'
)
group by 2, 3, 4
