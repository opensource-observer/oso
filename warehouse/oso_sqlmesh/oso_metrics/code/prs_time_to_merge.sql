select
    @metrics_sample_date(time) as metrics_sample_date,
    event_source,
    to_artifact_id,
    '' as from_artifact_id,
    @metric_name() as metric,
    avg(created_delta) as amount
from oso.int_issue_event_time_deltas
where
    event_type = 'PULL_REQUEST_MERGED'
    and `time` between @metrics_start('DATE') and @metrics_end('DATE')
group by 1, metric, from_artifact_id, to_artifact_id, event_source,
