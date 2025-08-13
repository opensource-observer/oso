select
    @metrics_sample_date(events.time) as metrics_sample_date,
    events.event_source,
    events.to_artifact_id,
    '' as from_artifact_id,
    @metric_name() as metric,
    approx_distinct(events.from_artifact_id) as amount
from oso.int_worldchain_events_by_project as events
where
    events.event_type = 'WORLDCHAIN_VERIFIED_USEROP'
    and events.time between @metrics_start('DATE') and @metrics_end('DATE')
group by 1, metric, from_artifact_id, to_artifact_id, event_source,
