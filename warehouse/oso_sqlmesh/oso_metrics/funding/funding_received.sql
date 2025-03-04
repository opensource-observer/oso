select @metrics_sample_date(events.bucket_day) as metrics_sample_date,
  events.event_source,
  events.to_artifact_id,
  '' as from_artifact_id,
  @metric_name() as metric,
  SUM(events.amount) as amount
from metrics.int_events_daily_to_artifact as events
where event_type = 'CREDIT'
  and events.bucket_day BETWEEN @metrics_start('DATE') AND @metrics_end('DATE')
group by 1,
  metric,
  from_artifact_id,
  to_artifact_id,
  event_source
