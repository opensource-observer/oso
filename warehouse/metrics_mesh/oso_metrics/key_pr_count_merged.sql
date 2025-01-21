select distinct
  now() as metrics_sample_date,
  events.event_source,
  events.to_artifact_id,
  '' as from_artifact_id,
  @metric_name('pr_count_merged') as metric,
  count(*) as amount
from metrics.events_daily_to_artifact as events
where event_type = 'PULL_REQUEST_MERGED'
group by 2, 3
