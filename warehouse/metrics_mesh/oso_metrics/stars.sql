select @TIME_AGGREGATION_BUCKET(@end_ds, @time_aggregation) as metrics_sample_date,
  events.event_source,
  events.to_artifact_id,
  '' as from_artifact_id,
  @metric_name() as metric,
  SUM(events.amount) as amount
from metrics.events_daily_to_artifact as events
where event_type in ('STARRED')
  and events.bucket_day BETWEEN STR_TO_DATE(@start_ds, '%Y-%m-%d') AND STR_TO_DATE(@end_ds, '%Y-%m-%d')
group by 1,
  metric,
  from_artifact_id,
  to_artifact_id,
  event_source