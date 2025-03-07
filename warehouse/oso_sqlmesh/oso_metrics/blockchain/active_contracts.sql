select
    @metrics_sample_date(events.bucket_day) as metrics_sample_date,
    events.event_source,
    events.to_artifact_id as to_artifact_id,
    '' as from_artifact_id,
    @metric_name() as metric,
    count(distinct events.to_artifact_id) as amount
from oso.int_events_daily__blockchain as events
where
    events.event_type in ('CONTRACT_INVOCATION')
    and events.bucket_day between @metrics_start('DATE') and @metrics_end('DATE')
group by 1, metric, from_artifact_id, to_artifact_id, event_source
