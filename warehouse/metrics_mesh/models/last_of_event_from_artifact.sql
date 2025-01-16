MODEL (
  name metrics.last_of_event_from_artifact,
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
FROM @oso_source('bigquery.oso.timeseries_events_by_artifact_v0')
GROUP BY
  event_type,
  event_source,
  from_artifact_id,
  to_artifact_id