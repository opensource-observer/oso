select
    @metrics_sample_date(events.time) as metrics_sample_date,
    events.event_source,
    events.to_artifact_id,
    events.from_artifact_id,
    @metric_name() as metric,
    sum(events.amount) as amount,
    'USD' as unit
from oso.int_events__funding_awarded as events
where
    event_type = 'FUNDING_AWARDED'
    and events.time between @metrics_start('DATE') and @metrics_end('DATE')
group by 1, metric, from_artifact_id, to_artifact_id, event_source
