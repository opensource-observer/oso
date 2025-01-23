select distinct
  now() as metrics_sample_date,
  events.event_source,
  events.to_artifact_id,
  '' as from_artifact_id,
  @metric_name('active_address_count') as metric,
  count(distinct events.from_artifact_id) as amount
from metrics.events_daily_to_artifact as events
where event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
group by 2, 3
