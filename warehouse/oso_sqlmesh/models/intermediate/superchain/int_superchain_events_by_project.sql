MODEL (
  name oso.int_superchain_events_by_project,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 180,
    batch_concurrency 1
  ),
  start '2021-10-01',
  cron '@daily',
  partitioned_by (DAY("bucket_day"), "event_type", "event_source"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id)
);

WITH unioned_events AS (
  SELECT * FROM oso.int_events_daily__4337
  UNION ALL
  SELECT * FROM oso.int_events_daily__blockchain
)

SELECT
  e.bucket_day,
  e.event_type,
  e.event_source,
  e.from_artifact_id,
  e.to_artifact_id,
  e.amount,
  e.count,
  abp.project_id as project_id
FROM unioned_events AS e
INNER JOIN oso.artifacts_by_project_v1 AS abp
ON e.to_artifact_id = abp.artifact_id
WHERE e.bucket_day BETWEEN @start_dt AND @end_dt
