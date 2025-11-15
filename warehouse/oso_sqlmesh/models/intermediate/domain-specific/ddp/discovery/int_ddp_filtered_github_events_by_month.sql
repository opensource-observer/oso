MODEL (
  name oso.int_ddp_filtered_github_events_by_month,
  description "GitHub events aggregated by month, filtered on developers who have interacted with a repo in the Ethereum ecosystem",
  kind FULL,
  dialect trino,
  grain (bucket_month, event_type, git_user, repo_artifact_id),
  tags (
    'entity_category=artifact'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH base_events AS (
  SELECT
    e.bucket_month,
    e.event_type,
    u.artifact_name AS git_user,
    e.to_artifact_id AS repo_artifact_id,
    e.amount
  FROM oso.int_events_monthly__github AS e
  JOIN oso.int_github_users_bot_filtered AS u
    ON e.from_artifact_id = u.artifact_id
  WHERE
    NOT u.is_bot
    AND e.event_type IN (
      'STARRED',
      'FORKED',
      'ISSUE_OPENED',
      'PULL_REQUEST_OPENED',
      'COMMIT_CODE'
    )
),

-- First pass: find developers who have interacted with a pretrust repo
devs_touching_pretrust AS (
  SELECT DISTINCT git_user
  FROM base_events
  WHERE repo_artifact_id IN (
    SELECT repo_artifact_id
    FROM oso.int_ddp_repo_pretrust
    WHERE raw_score > 0
  )
)

-- Second pass: build edges for those devs to any repos they touched
SELECT
  bucket_month,
  event_type,
  git_user,
  repo_artifact_id,
  amount
FROM base_events
WHERE git_user IN (
  SELECT git_user
  FROM devs_touching_pretrust
)