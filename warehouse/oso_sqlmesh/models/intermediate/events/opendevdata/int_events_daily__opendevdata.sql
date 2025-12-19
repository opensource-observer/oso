MODEL (
  name oso.int_events_daily__opendevdata,
  description 'Daily aggregation of OpenDevData events',
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  activity.day AS bucket_day,
  COALESCE(users.artifact_id, CAST(activity.canonical_developer_id AS VARCHAR)) AS from_artifact_id,
  repos.artifact_id AS to_artifact_id,
  'OPENDEVDATA' AS event_source,
  'COMMIT_CODE' AS event_type,
  SUM(activity.num_commits) AS amount
FROM oso.stg_opendevdata__repo_developer_activities AS activity
JOIN oso.int_repositories__opendevdata AS repos
  ON activity.repo_id = repos.repository_id
LEFT JOIN oso.int_github_users__opendevdata AS users
  ON activity.canonical_developer_id = users.canonical_developer_id
WHERE
  activity.num_commits > 0
GROUP BY
  activity.day,
  COALESCE(users.artifact_id, CAST(activity.canonical_developer_id AS VARCHAR)),
  repos.artifact_id
