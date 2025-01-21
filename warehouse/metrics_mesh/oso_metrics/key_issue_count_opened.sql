select distinct
  now() as metrics_sample_date,
  events.event_source,
  events.to_artifact_id,
  '' as from_artifact_id,
  @metric_name('issue_count_opened') as metric,
  count(*) as amount
from metrics.events_daily_to_artifact as events
where event_type = 'ISSUE_OPENED'
group by 2, 3
