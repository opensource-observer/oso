-- TODO (@ravenac95) keeping this for now, might prove useful, but we likely need
-- a different kind of model for first commit data
select @metrics_sample_date(events.bucket_day) as metrics_sample_date,
  events.event_source,
  events.to_artifact_id as to_artifact_id,
  '' as from_artifact_id,
  @metric_name() as metric,
  1 as amount,
  MIN(events.bucket_day) as first_commit_date
from metrics.events_daily_to_artifact as events
where events.event_type = 'COMMIT_CODE'
  and events.bucket_day BETWEEN @metrics_start('DATE') AND @metrics_end('DATE')
group by 1,
  metric,
  from_artifact_id,
  to_artifact_id,
  event_source