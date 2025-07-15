select
  @metrics_sample_date(pr_events.time) as metrics_sample_date,
  pr_events.event_source,
  pr_events.to_artifact_id,
  '' as from_artifact_id,
  @metric_name() as metric,
  count(distinct pr_events.from_artifact_id) as amount
from oso.int_events_aux_prs as pr_events
where
  pr_events.time between @metrics_start('DATE') and @metrics_end('DATE')
  and pr_events.event_type = 'PULL_REQUEST_OPENED'
  and pr_events.author_association = 'FIRST_TIME_CONTRIBUTOR'
group by 1, 2, 3, 4, 5
