/* Model that records the delta (in seconds) since the creation of the issue or */
/* pr. */
model(
    name oso.int_issue_event_time_deltas,
    kind incremental_by_time_range(
        time_column time, batch_size 365, batch_concurrency 1
    ),
    start '2015-01-01',
    cron '@daily',
    partitioned_by(day("time"), "event_type"),
    grain(time, event_type, event_source, from_artifact_id, to_artifact_id)
)
;

select
    "time",
    event_type,
    event_source,
    @oso_id(event_source, to_artifact_id, issue_number) as issue_id,
    issue_number,
    to_artifact_id,
    from_artifact_id,
    created_at::timestamp,
    merged_at::timestamp,
    closed_at::timestamp,
    date_diff('SECOND', created_at, "time")::double as created_delta,
    case
        when merged_at is null then null else date_diff('SECOND', merged_at, "time")
    end::double as merged_delta,
    case
        when closed_at is null then null else date_diff('SECOND', closed_at, "time")
    end::double as closed_delta,
    comments::double
from oso.int_events_aux_issues
where "time" between @start_dt and @end_dt
