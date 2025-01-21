select distinct
  now() as metrics_sample_date,
  events.event_source,
  events.to_artifact_id,
  '' as from_artifact_id,
  @metric_name('developer_count') as metric,
  count(distinct from_artifact_id) as amount
from metrics.events_daily_to_artifact as events
where event_type in (
  'COMMIT_CODE',
  'PULL_REQUEST_OPENED'
)
group by 2, 3
