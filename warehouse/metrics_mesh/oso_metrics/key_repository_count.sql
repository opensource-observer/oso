select distinct
  now() as metrics_sample_date,
  events.event_source,
  events.to_artifact_id,
  '' as from_artifact_id,
  @metric_name('repository_count') as metric,
  count(distinct events.to_artifact_id) as amount
from metrics.events_daily_to_artifact as events
where events.event_type in (
  'ISSUE_OPENED',
  'STARRED',
  'PULL_REQUEST_OPENED',
  'FORKED',
  'PULL_REQUEST_REOPENED',
  'PULL_REQUEST_CLOSED',
  'COMMIT_CODE',
  'ISSUE_REOPENED',
  'PULL_REQUEST_MERGED',
  'ISSUE_CLOSED'
)
group by 2, 3
