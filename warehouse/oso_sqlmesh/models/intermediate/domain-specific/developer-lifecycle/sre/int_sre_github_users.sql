MODEL(
  name oso.int_sre_github_users,
  description 'Speedrun Ethereum GitHub Users',
  dialect trino,
  kind full,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH sre_github_users AS (
  SELECT
    LOWER(github_handle) AS github_handle,
    CAST(CAST(createdAt AS TIMESTAMP) AS DATE) AS created_at,
    referrer,
    COALESCE(challengesCompleted, 0) AS challenges_completed,
    batchId AS batch_id
  FROM oso.seed_sre_github_users
)

SELECT
  @oso_entity_id('GITHUB', github_handle, github_handle) AS artifact_id,
  github_handle,
  created_at,
  referrer,
  challenges_completed,
  batch_id
FROM sre_github_users
