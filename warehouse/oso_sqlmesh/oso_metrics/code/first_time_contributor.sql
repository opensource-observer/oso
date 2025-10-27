with first_contribution as (
    select
        from_artifact_id,
        min(bucket_day) as first_contribution_date
    from oso.int_events_daily__github
    where
        event_type
        in ('COMMIT_CODE', 'ISSUE_OPENED', 'PULL_REQUEST_OPENED', 'PULL_REQUEST_MERGED')
    group by 1
)
select
    @metrics_sample_date(events.bucket_day) as metrics_sample_date,
    events.event_source,
    events.to_artifact_id as to_artifact_id,
    '' as from_artifact_id,
    @metric_name() as metric,
    count(distinct events.from_artifact_id) as amount
from oso.int_events_daily__github as events
inner join
    first_contribution
    on
        events.from_artifact_id = first_contribution.from_artifact_id
        and events.bucket_day = first_contribution.first_contribution_date
where
    events.event_type
    in ('COMMIT_CODE', 'ISSUE_OPENED', 'PULL_REQUEST_OPENED', 'PULL_REQUEST_MERGED')
    and events.bucket_day between @metrics_start('DATE') and @metrics_end('DATE')
group by 1, metric, from_artifact_id, to_artifact_id, event_source
