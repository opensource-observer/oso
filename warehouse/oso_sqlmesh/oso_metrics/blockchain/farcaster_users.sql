select
    @metrics_sample_date(events.bucket_day) as metrics_sample_date,
    events.event_source,
    events.to_artifact_id,
    '' as from_artifact_id,
    @metric_name('farcaster_users') as metric,
    approx_distinct(users.user_id) as amount
from oso.int_events_daily__l2_internal_transactions as events
join oso.int_artifacts_by_farcaster_user as users
  on events.from_artifact_id = users.artifact_id
where
    events.bucket_day between @metrics_start('DATE') and @metrics_end('DATE')
group by 1, metric, from_artifact_id, events.to_artifact_id, event_source
