MODEL (
  name oso.int_github_users__opendevdata,
  description 'All GitHub users in OpenDevData',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH commit_developers AS (
  SELECT DISTINCT
    commits.canonical_developer_id,
    LOWER(commits.commit_author_name) AS artifact_name,
    commits.commit_author_name AS display_name,
    commits.commit_author_email AS email,
    CAST(commits.is_bot = 1 AS BOOLEAN) AS is_bot,
    developers.primary_github_user_id AS primary_github_user_id,
    developers.primary_developer_email_identity_id
      AS primary_developer_email_identity_id
  FROM oso.stg_opendevdata__commits AS commits
  JOIN oso.stg_opendevdata__canonical_developers AS developers
    ON commits.canonical_developer_id = developers.id
),

github_users AS (
  SELECT DISTINCT
    canonical_developer_id,
    @oso_entity_id('GITHUB', artifact_name, artifact_name) AS artifact_id,
    'GIT_USER' AS artifact_type,
    'https://github.com/' || artifact_name AS artifact_url
  FROM commit_developers
)

SELECT
  github_users.artifact_id,
  commit_developers.artifact_name AS artifact_namespace,
  commit_developers.artifact_name,
  github_users.artifact_type,
  github_users.artifact_url,
  commit_developers.display_name,
  commit_developers.email,
  commit_developers.is_bot,
  canonical_developer_id,
  commit_developers.primary_github_user_id,
  commit_developers.primary_developer_email_identity_id
FROM github_users
JOIN commit_developers USING (canonical_developer_id)