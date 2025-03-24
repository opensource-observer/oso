select
    @metrics_sample_date(events.bucket_day) as metrics_sample_date,
    UPPER(events.from_artifact_namespace) as event_source,
    events.to_artifact_id,
    '' as from_artifact_id,
    @metric_name() as metric,
    sum(events.amount) / @metrics_sample_interval_length('day') as amount
from oso.int_events_daily__defillama_tvl as events
where
    events.bucket_day between @metrics_start('DATE') and @metrics_end('DATE')
group by 1, 2, 3, 4, 5
