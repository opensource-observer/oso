select 
  @metrics_sample_date(merged_events.time) as metrics_sample_date, -- we use PR merge event tiemstamp (note: we haven't bucketed by day in the events table)
  merged_events.event_source,
  merged_events.to_artifact_id,
  '' as from_artifact_id,
  @metric_name() as metric,
  AVG(TIMESTAMP_DIFF(merged_events.time, pr_events.time, minute) / 60.0 / 24.0) as amount
from (
  select
    number,
    to_artifact_id,
    time,
    event_source
  from metrics.timeseries_events_aux_issues_by_artifact_v0
  where event_type = 'PULL_REQUEST_OPENED'
) as pr_events
inner join (
  select
    number,
    to_artifact_id,
    time,
    event_source
  from metrics.timeseries_events_aux_issues_by_artifact_v0
  where event_type = 'PULL_REQUEST_MERGED'
) as merged_events
on pr_events.number = merged_events.number
and pr_events.to_artifact_id = merged_events.to_artifact_id
where merged_events.time BETWEEN @metrics_start('DATE') AND @metrics_end('DATE')
group by 
  metrics_sample_date,
  merged_events.event_source,
  merged_events.to_artifact_id,
  from_artifact_id,
  metric
