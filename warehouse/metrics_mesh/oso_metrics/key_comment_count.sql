select distinct
  now() as metrics_sample_date,
  events.event_source,
  events.to_artifact_id,
  '' as from_artifact_id,
  @metric_name('comment_count') as metric,
  count(*) as amount
from metrics.events_daily_to_artifact as events
where event_type in (
  'PULL_REQUEST_REVIEW_COMMENT',
  'ISSUE_COMMENT'
)
group by 2, 3
