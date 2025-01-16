select distinct
  now() as metrics_sample_date,
  events.event_source,
  events.to_artifact_id,
  '' as from_artifact_id,
  @metric_name('first_commit') as metric,
  @to_unix_timestamp(min(events.bucket_day)) as amount
from metrics.events_daily_to_artifact as events
where event_type = 'COMMIT_CODE'
group by 2, 3
