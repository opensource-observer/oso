MODEL (
  name oso.int_last_of_event_from_artifact__github,
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
  MAX(bucket_day) AS time,
  event_type,
  event_source,
  from_artifact_id,
  to_artifact_id
FROM oso.int_events_daily__github
GROUP BY
  event_type,
  event_source,
  from_artifact_id,
  to_artifact_id