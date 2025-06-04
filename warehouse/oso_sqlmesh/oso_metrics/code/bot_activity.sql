select
    @metrics_sample_date(events.bucket_day) as metrics_sample_date,
    events.event_source,
    events.to_artifact_id,
    '' as from_artifact_id,
    @metric_name() as metric,
    sum(events.amount) as amount
from oso.int_events_daily__github as events
inner join oso.int_github_users_bot_filtered as bots
    on events.from_artifact_id = bots.artifact_id
where
    bots.is_bot = true
    and events.bucket_day between @metrics_start('DATE') and @metrics_end('DATE')
group by 1, metric, from_artifact_id, to_artifact_id, event_source
