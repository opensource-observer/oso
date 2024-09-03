select @end_date as bucket_day,
  events.event_source,
  events.to_artifact_id,
  events.from_artifact_id,
  @metric_name as metric,
  COUNT(DISTINCT events.bucket_day) amount,
  from metrics.events_daily_to_artifact as events
where event_type in @activity_event_types
  and events.bucket_day BETWEEN (@end_date - INTERVAL @trailing_days DAY)
  AND @end_date
group by 1,
  metric,
  from_artifact_id,
  to_artifact_id,
  event_source,