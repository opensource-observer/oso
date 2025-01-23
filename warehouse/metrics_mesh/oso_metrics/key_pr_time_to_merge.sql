select distinct
  now() as metrics_sample_date,
  event_source,
  events.to_artifact_id,
  '' as from_artifact_id,
  @metric_name('pr_time_to_merge') as metric,
  avg(created_delta) as amount
from metrics.issue_event_time_deltas as events 
where event_type = 'PULL_REQUEST_MERGED'
group by 2, 3
