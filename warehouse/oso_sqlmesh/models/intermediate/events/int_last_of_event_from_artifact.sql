MODEL (
  name oso.int_last_of_event_from_artifact,
  kind FULL,
  partitioned_by (YEAR("time"), "event_type", "event_source"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id)
);

SELECT
  MAX(bucket_week) AS time,
  event_type,
  event_source,
  from_artifact_id,
  to_artifact_id
FROM oso.int_events_weekly_to_artifact
GROUP BY
  event_type,
  event_source,
  from_artifact_id,
  to_artifact_id