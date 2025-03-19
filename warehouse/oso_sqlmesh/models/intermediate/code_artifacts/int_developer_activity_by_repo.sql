MODEL (
  name oso.int_developer_activity_by_repo,
  description 'Summarizes developer activity by repository in OSSD',
  kind FULL,
);

WITH deveopers AS (
  SELECT
    users.user_id AS developer_id,
    users.github_username AS developer_name,
    events.to_artifact_id AS repo_artifact_id
  FROM oso.int_events_filtered__github AS events
  JOIN oso.int_github_users AS users
    ON events.from_artifact_id = users.user_id
  WHERE
    NOT users.is_bot
    AND events.event_type = 'COMMIT_CODE'
)

SELECT
  events.to_artifact_id AS repo_artifact_id,
  developers.developer_id,
  developers.developer_name,
  events.event_type,
  MIN(events.time) AS first_event,
  MAX(events.time) AS last_event,
  SUM(events.amount) AS total_events
FROM oso.int_events_filtered__github AS events
INNER JOIN developers
  ON events.from_artifact_id = developers.developer_id
GROUP BY
  events.to_artifact_id,
  developers.developer_id,
  developers.developer_name,
  events.event_type