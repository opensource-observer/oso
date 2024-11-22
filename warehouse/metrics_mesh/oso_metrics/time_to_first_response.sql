select 
  @metrics_sample_date(time_to_first_response_events.responded_at) as metrics_sample_date, 
  time_to_first_response_events.event_source,
  time_to_first_response_events.to_artifact_id,
  '' as from_artifact_id,
  @metric_name() as metric,
  AVG(time_to_first_response_events.amount) as amount
from (
  select
    responded_at,
    to_artifact_id,
    event_source,
    time_to_first_response_days as amount
  from (
    select
      start_events.issue_number,
      start_events.to_artifact_id,
      start_events.created_at,
      start_events.event_source,
      min(resp.responded_at) as responded_at,
      cast(
        timestamp_diff(min(resp.responded_at), start_events.created_at, minute)
        as float64
      ) / 60.0 / 24.0 as time_to_first_response_days
    from (
      select
        issue_number,
        from_artifact_id as creator_id,
        to_artifact_id,
        time,
        event_type
      from metrics.timeseries_events_aux_issues_by_artifact_v0
      where event_type in ('PULL_REQUEST_OPENED', 'ISSUE_OPENED')
    ) as start_events
    inner join (
      select
        issue_number,
        from_artifact_id as responder_id,
        to_artifact_id,
        time as responded_at,
        event_type
      from metrics.timeseries_events_aux_issues_by_artifact_v0
      where event_type in (
        'PULL_REQUEST_MERGED',
        'PULL_REQUEST_REVIEW_COMMENT',
        'ISSUE_CLOSED',
        'ISSUE_COMMENT'
      )
    ) as resp_events
    on
      start_events.issue_number = resp_events.issue_number
      and start_events.to_artifact_id = resp_events.to_artifact_id
      and start_events.creator_id != resp_events.responder_id
      and (
        (
          start_events.event_type = 'ISSUE_OPENED'
          and resp_events.event_type in (
            'ISSUE_COMMENT', 'ISSUE_CLOSED'
          )
        )
        or
        (
          start_events.event_type = 'PULL_REQUEST_OPENED'
          and resp_events.event_type in (
            'PULL_REQUEST_REVIEW_COMMENT', 'PULL_REQUEST_MERGED'
          )
        )
      )
    group by
      start_events.issue_number,
      start_events.to_artifact_id,
      start_events.created_at
  ) as time_to_first_response
) as time_to_first_response_events
where time_to_first_response_events.responded_at BETWEEN @metrics_start('DATE') AND @metrics_end('DATE')
group by 
  metrics_sample_date,
  time_to_first_response_events.event_source,
  time_to_first_response_events.to_artifact_id,
  from_artifact_id,
  metric
