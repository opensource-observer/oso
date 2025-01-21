select distinct
  now() as metrics_sample_date,
  events.event_source,
  events.to_artifact_id,
  '' as from_artifact_id,
  @metric_name('funding_received') as metric,
  sum(events.amount) as amount
from metrics.events_daily_to_artifact as events
where event_type = 'CREDIT'
group by 2, 3
