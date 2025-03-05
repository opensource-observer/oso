MODEL (
  name oso.int_artifacts_history,
  description 'Currently this only captures the history of git_users. It does not capture git_repo naming histories.',
  kind FULL
);

WITH user_events AS (
  /* `from` actor artifacts derived from all events */
  SELECT
    event_source AS artifact_source,
    from_artifact_source_id AS artifact_source_id,
    from_artifact_type AS artifact_type,
    from_artifact_namespace AS artifact_namespace,
    from_artifact_name AS artifact_name,
    '' AS artifact_url,
    time
  FROM oso.int_events
)
SELECT
  LOWER(artifact_source_id) AS artifact_source_id,
  UPPER(artifact_source) AS artifact_source,
  UPPER(artifact_type) AS artifact_type,
  LOWER(artifact_namespace) AS artifact_namespace,
  LOWER(artifact_url) AS artifact_url,
  LOWER(artifact_name) AS artifact_name,
  MAX(time) AS last_used,
  MIN(time) AS first_used
FROM user_events
GROUP BY
  artifact_source_id,
  artifact_source,
  artifact_type,
  artifact_namespace,
  artifact_url,
  artifact_name