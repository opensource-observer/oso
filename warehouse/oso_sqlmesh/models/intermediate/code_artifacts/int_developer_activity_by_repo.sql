MODEL (
  name oso.int_developer_activity_by_repo,
  description 'Summarizes developer activity by repository',
  kind FULL
);

WITH developers AS (
  SELECT DISTINCT
    users.user_id AS developer_id,
    users.display_name AS developer_name,
    events.to_artifact_id AS repo_artifact_id
  FROM oso.int_events__github AS events
  INNER JOIN oso.int_users AS users
    ON events.from_artifact_id = users.user_id
  WHERE
    events.event_type = 'COMMIT_CODE'
    AND NOT REGEXP_MATCHES(LOWER(users.display_name), '(^|[^a-z0-9_])bot([^a-z0-9_]|$)|bot$')
)
SELECT
  events.to_artifact_id AS repo_artifact_id,
  developers.developer_id,
  developers.developer_name,
  events.event_type,
  MIN(events.time) AS first_event,
  MAX(events.time) AS last_event,
  COUNT(DISTINCT events.time) AS total_events
FROM oso.int_events__github AS events
INNER JOIN developers
  ON events.from_artifact_id = developers.developer_id
GROUP BY
  events.to_artifact_id,
  developers.developer_id,
  developers.developer_name,
  events.event_type