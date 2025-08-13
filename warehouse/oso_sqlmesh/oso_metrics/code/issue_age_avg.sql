SELECT
  @metrics_sample_date("time") as metrics_sample_date,
  event_source,
  to_artifact_id,
  '' AS from_artifact_id,
  @metric_name() as metric,
  AVG(created_delta)::DOUBLE as amount
FROM oso.int_issue_event_time_deltas
WHERE
  "time" BETWEEN @metrics_start('TIMESTAMP') AND @metrics_end('TIMESTAMP')
  AND created_delta IS NOT NULL
GROUP BY
  @metrics_sample_date("time"),
  event_source,
  to_artifact_id,
  from_artifact_id
