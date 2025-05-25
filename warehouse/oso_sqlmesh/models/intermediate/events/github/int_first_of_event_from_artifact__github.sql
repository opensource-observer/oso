MODEL (
  name oso.int_first_of_event_from_artifact__github,
  kind FULL,
  partitioned_by (YEAR("time"), "event_type", "event_source"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id),
  audits (
    not_null(columns := (event_type, event_source))
  ),
  tags (
    "github",
  ),
);

SELECT
  MIN(bucket_week) AS time,
  event_type,
  event_source,
  from_artifact_id,
  to_artifact_id
FROM oso.int_events_weekly__github
GROUP BY
  event_type,
  event_source,
  from_artifact_id,
  to_artifact_id