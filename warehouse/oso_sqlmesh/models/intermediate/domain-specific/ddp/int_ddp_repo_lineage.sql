MODEL (
  name oso.int_ddp_repo_lineage,
  description "Repository lineage tracking for DDP repos, identifying renamed repositories based on shared GitHub source IDs and commit activity",
  kind FULL,
  dialect trino,
  grain (artifact_id),
  tags (
    'entity_category=artifact'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

-- Get base DDP repositories with metadata
WITH ddp_repos AS (
  SELECT
    artifact_id,
    artifact_source_id,
    artifact_namespace,
    artifact_name,
    artifact_url,
    updated_at
  FROM oso.int_ddp_repo_metadata
),

-- Get commit timing data for repos
repo_commits AS (
  SELECT
    artifact_id,
    artifact_source_id,
    last_commit_time
  FROM oso.int_first_last_commit_to_github_repository
),

-- Join repos with their commit activity
repos_with_activity AS (
  SELECT
    r.artifact_id,
    r.artifact_source_id,
    r.artifact_namespace,
    r.artifact_name,
    r.artifact_url,
    r.updated_at,
    c.last_commit_time
  FROM ddp_repos AS r
  LEFT JOIN repo_commits AS c
    ON r.artifact_id = c.artifact_id
),

-- Rank repos within each artifact_source_id to find the current one(s)
-- Lower rank = more current (ordered by last_commit_time DESC, updated_at DESC)
ranked_repos AS (
  SELECT
    artifact_id,
    artifact_source_id,
    artifact_namespace,
    artifact_name,
    artifact_url,
    updated_at,
    last_commit_time,
    RANK() OVER (
      PARTITION BY artifact_source_id
      ORDER BY
        last_commit_time DESC NULLS LAST,
        updated_at DESC NULLS LAST
    ) AS repo_rank
  FROM repos_with_activity
),

-- Get the artifact_url(s) of current repos for each source_id
current_repo_urls AS (
  SELECT
    artifact_source_id,
    MIN(artifact_url) AS current_url
  FROM ranked_repos
  WHERE repo_rank = 1
  GROUP BY artifact_source_id
)

SELECT
  r.artifact_id,
  r.artifact_source_id,
  r.artifact_namespace,
  r.artifact_name,
  -- Mark as current if it has rank 1 (highest activity)
  CAST(r.repo_rank = 1 AS BOOLEAN) AS is_current,
  -- If not current, provide the URL of the current repo
  CASE
    WHEN r.repo_rank = 1 THEN NULL
    ELSE c.current_url
  END AS renamed_to
FROM ranked_repos AS r
LEFT JOIN current_repo_urls AS c
  ON r.artifact_source_id = c.artifact_source_id

