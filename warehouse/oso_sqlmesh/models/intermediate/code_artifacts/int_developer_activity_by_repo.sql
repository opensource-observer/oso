MODEL (
  name oso.int_developer_activity_by_repo,
  description 'Summarizes developer activity by repository in OSSD',
  partitioned_by (YEAR("first_event"), "event_type"),
  grain (first_event, repo_artifact_id, developer_id, developer_name, event_type),
  kind FULL,
  dialect trino,
);

WITH developers AS (
  SELECT DISTINCT
    u.user_id AS developer_id,
    u.github_username AS developer_name
  FROM oso.int_first_of_event_from_artifact__github AS e
  JOIN oso.int_github_users AS u
    ON e.from_artifact_id = u.user_id
  WHERE
    NOT u.is_bot
    AND e.event_type = 'COMMIT_CODE'
    AND e.event_source = 'GITHUB'
),

all_events AS (
  SELECT 
    fe.from_artifact_id,
    fe.to_artifact_id,
    fe.event_type,
    fe.time AS first_event,
    le.time AS last_event
  FROM oso.int_first_of_event_from_artifact__github AS fe
  JOIN oso.int_last_of_event_from_artifact__github AS le
    ON fe.from_artifact_id = le.from_artifact_id
    AND fe.to_artifact_id = le.to_artifact_id
    AND fe.event_type = le.event_type
  WHERE fe.event_source = 'GITHUB'
)

SELECT
  ae.to_artifact_id AS repo_artifact_id,
  d.developer_id,
  d.developer_name,
  ae.event_type,
  ae.first_event,
  ae.last_event
FROM all_events AS ae
JOIN developers AS d
  ON ae.from_artifact_id = d.developer_id