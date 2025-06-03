select
    @metrics_sample_date(events.bucket_day) as metrics_sample_date,
    events.event_source,
    events.to_artifact_id,
    events.from_artifact_id,
    @metric_name() as metric,
    sum(events.amount) as amount,
    'USD' as unit
from oso.int_events_daily__funding as events
where
    event_type = 'FUNDING_AWARDED'
    and events.bucket_day between @metrics_start('DATE') and @metrics_end('DATE')
group by 1, metric, from_artifact_id, to_artifact_id, event_source
