select
  bucket_day,
  event_source,
  to_artifact_id,
  from_artifact_id,
  @metric_name as metric,
  COUNT(DISTINCT bucket_day) amount,
from metrics.int_events_daily_to_artifact
where event_type = @activity_event_type and
  bucket_day BETWEEN (@end_date - INTERVAL @trailing_days DAY) AND @end_date
group by
  metric,
  from_artifact_id,
  to_artifact_id,
  event_source,
  bucket_day