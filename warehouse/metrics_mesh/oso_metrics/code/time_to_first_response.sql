select @metrics_sample_date(time) as metrics_sample_date,
  event_source,
  to_artifact_id,
  '' as from_artifact_id,
  @metric_name() as metric,
  AVG(created_delta) as amount
from metrics.int_issue_event_time_deltas
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
  and `time` BETWEEN @metrics_start('DATE') and @metrics_end('DATE')
group by 1,
  metric,
  from_artifact_id,
  to_artifact_id,
  event_source,
