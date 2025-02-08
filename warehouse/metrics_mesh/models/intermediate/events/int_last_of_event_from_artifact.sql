MODEL (
  name metrics.int_last_of_event_from_artifact,
  kind FULL,
  partitioned_by (YEAR("time"), "event_type", "event_source"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id)
);

SELECT
  MAX(time) AS time,
  event_type,
  event_source,
  from_artifact_id,
  to_artifact_id
FROM metrics.int_events
GROUP BY
  event_type,
  event_source,
  from_artifact_id,
  to_artifact_id
