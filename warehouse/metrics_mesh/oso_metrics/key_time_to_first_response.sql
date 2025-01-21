select distinct
  now() as metrics_sample_date,
  event_source,
  events.to_artifact_id,
  '' as from_artifact_id,
  @metric_name('time_to_first_response') as metric,
  avg(created_delta) as amount
from metrics.issue_event_time_deltas
where (
    (
      event_type in ('PULL_REQUEST_MERGED', 'ISSUE_CLOSED')
      and comments = 0
    )
    or (
      event_type in ('PULL_REQUEST_REVIEW_COMMENT', 'ISSUE_COMMENT')
      and comments = 1
    )
)
group by 2, 3
