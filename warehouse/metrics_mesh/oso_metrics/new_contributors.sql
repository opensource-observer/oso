with first_contributions as (
    select
        events.from_artifact_id as contributor_id,
        events.to_artifact_id as project_id,
        MIN(events.bucket_day) as first_contribution_date
    from metrics.events_daily_to_artifact as events
    where events.event_type in ('COMMIT_CODE', 'ISSUE_OPENED', 'PULL_REQUEST_OPENED', 'PULL_REQUEST_MERGED')
      and events.bucket_day < @metrics_end(DATE)
    group by events.from_artifact_id, events.to_artifact_id
)

select 
    @metrics_sample_date(events.bucket_day) as metrics_sample_date,
    events.event_source,
    events.to_artifact_id as project_id,
    '' as from_artifact_id,
    @metric_name() as metric,
    COUNT(distinct fc.contributor_id) as new_contributor_count
from metrics.events_daily_to_artifact as events
join first_contributions as fc
    on events.from_artifact_id = fc.contributor_id 
    and events.to_artifact_id = fc.project_id
where fc.first_contribution_date BETWEEN @metrics_start(DATE) AND @metrics_end(DATE)
group by 1,
    metric,
    from_artifact_id,
    project_id,
    event_source
