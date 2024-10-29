select @metrics_sample_date(events.bucket_day) as metrics_sample_date,
  events.event_source,
  events.to_artifact_id as project_id,
  '' as from_artifact_id,
  @metric_name() as metric,
  COUNT(distinct events.from_artifact_id) as contributor_count
from metrics.events_daily_to_artifact as events
where events.event_type in (
  'COMMIT_CODE',
  'ISSUE_OPENED',
  'PULL_REQUEST_OPENED',
  'PULL_REQUEST_MERGED'
  )
  and events.bucket_day BETWEEN @metrics_start(DATE) AND @metrics_end(DATE)
group by 1,
  metric,
  from_artifact_id,
  project_id,
  event_source
