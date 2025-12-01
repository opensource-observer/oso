MODEL (
  name oso.int_ddp_repo_pretrust,
  description "Pre-trust scores for DDP repositories",
  kind FULL,
  dialect trino,
  grain (repo_artifact_id, url, raw_score, score),
  tags (
    'entity_category=artifact',
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  enabled false,
);

WITH repo_base AS (
  SELECT
    artifact_id AS repo_artifact_id,
    url,
    ln(1 + coalesce(star_count,0)) * 1.0
    + ln(1 + coalesce(fork_count,0)) * 1.5
    + CASE WHEN has_packages THEN 2.0 ELSE 0 END
    - CASE WHEN is_personal_repo THEN 2.0 ELSE 0 END AS raw_score
  FROM oso.int_ddp_repo_features
  WHERE is_ethereum
),
repo_norm AS (
  SELECT
    repo_artifact_id,
    url,
    raw_score,
    CASE 
      WHEN raw_score < 0 THEN 0
      ELSE raw_score / NULLIF(MAX(raw_score) OVER(), 0)
    END AS score
  FROM repo_base
)

SELECT DISTINCT
  repo_artifact_id,
  url,
  raw_score,
  score
FROM repo_norm
ORDER BY score DESC