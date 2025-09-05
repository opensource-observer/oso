select
    @metrics_sample_date(events.bucket_day) as metrics_sample_date,
    events.event_source,
    events.to_artifact_id,
    '' as from_artifact_id,
    @metric_name('layer2_gas_fees_amortized') as metric,
    sum(events.amortized_l2_gas_fee) as amount
from oso.int_events_daily__l2_internal_transactions as events
where
    events.bucket_day between @metrics_start('DATE') and @metrics_end('DATE')
group by 1, metric, from_artifact_id, to_artifact_id, event_source