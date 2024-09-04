select STR_TO_DATE(@end_ds, '%Y-%m-%d') as metrics_bucket_date,
  events.event_source,
  events.to_artifact_id,
  events.from_artifact_id,
  @metric_name as metric,
  COUNT(DISTINCT events.bucket_day) amount,
  from metrics.events_daily_to_artifact as events
where event_type in @activity_event_types
  and events.bucket_day BETWEEN (
    STR_TO_DATE(@end_ds, '%Y-%m-%d') - INTERVAL @trailing_days DAY
  )
  AND STR_TO_DATE(@end_ds, '%Y-%m-%d')
group by 1,
  metric,
  from_artifact_id,
  to_artifact_id,
  event_source,