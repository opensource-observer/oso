MODEL (
  name oso.int_project_to_projects__gitcoin,
  description 'Maps Gitcoin projects to OSO projects',
  dialect trino,
  kind FULL,
  audits (
    not_null(columns := (gitcoin_project_id, oso_project_id))
  )
);

WITH all_matches AS (
  SELECT
    git.project_id AS gitcoin_project_id,
    ossd.project_id AS oso_project_id,
    git.artifact_type AS artifact_type
  FROM oso.int_artifacts_by_project__gitcoin AS git
  JOIN oso.int_artifacts_by_project_in_ossd AS ossd
    ON git.artifact_id = ossd.artifact_id
   AND git.artifact_type = ossd.artifact_type
   AND git.artifact_type IN ('WALLET', 'SOCIAL_HANDLE', 'REPOSITORY')
),

agg AS (
  SELECT
    gitcoin_project_id,
    -- How many distinct OSO projects each Gitcoin project links to, by artifact type:
    COUNT(DISTINCT
      CASE WHEN artifact_type = 'WALLET' THEN oso_project_id END
    ) AS wallet_cnt,
    MIN(
      CASE WHEN artifact_type = 'WALLET' THEN oso_project_id END
    ) AS wallet_rep,
    COUNT(DISTINCT
      CASE WHEN artifact_type = 'SOCIAL_HANDLE' THEN oso_project_id END
    ) AS social_cnt,
    MIN(
      CASE WHEN artifact_type = 'SOCIAL_HANDLE' THEN oso_project_id END
    ) AS social_rep,
    COUNT(DISTINCT
      CASE WHEN artifact_type = 'REPOSITORY' THEN oso_project_id END
    ) AS repo_cnt,
    MIN(
      CASE WHEN artifact_type = 'REPOSITORY' THEN oso_project_id END
    ) AS repo_rep
  FROM all_matches
  GROUP BY gitcoin_project_id
),

chosen AS (
  SELECT
    gitcoin_project_id,
    -- Pick exactly one OSO project if it is the sole match at the highest‐priority artifact type:
    CASE
      WHEN wallet_cnt = 1 THEN wallet_rep
      WHEN wallet_cnt > 1 THEN NULL
      WHEN social_cnt = 1 THEN social_rep
      WHEN social_cnt > 1 THEN NULL
      WHEN repo_cnt = 1 THEN repo_rep
      ELSE NULL
    END AS best_oso_project_id
  FROM agg
),

all_pairs AS (
  SELECT
    abp_gitcoin.project_id AS gitcoin_project_id,
    abp_ossd.project_id AS oso_project_id,
    p_gitcoin.display_name AS gitcoin_project_name,
    p_oso.project_name AS oso_project_name,
    abp_gitcoin.artifact_type AS artifact_type,
    COUNT(DISTINCT abp_gitcoin.artifact_id) AS num_shared_artifacts
  FROM oso.int_artifacts_by_project__gitcoin AS abp_gitcoin
  JOIN oso.int_artifacts_by_project_in_ossd AS abp_ossd
    ON abp_gitcoin.artifact_id = abp_ossd.artifact_id
   AND abp_gitcoin.artifact_type = abp_ossd.artifact_type
   AND abp_gitcoin.artifact_type IN ('WALLET', 'SOCIAL_HANDLE', 'REPOSITORY')
  JOIN oso.int_projects__gitcoin AS p_gitcoin
    ON abp_gitcoin.project_id = p_gitcoin.project_id
  JOIN oso.projects_v1 AS p_oso
    ON abp_ossd.project_id = p_oso.project_id
  GROUP BY
    abp_gitcoin.project_id,
    abp_ossd.project_id,
    p_gitcoin.display_name,
    p_oso.project_name,
    abp_gitcoin.artifact_type
)

SELECT
  ap.gitcoin_project_id,
  ap.gitcoin_project_name,
  ap.oso_project_id,
  ap.oso_project_name,
  ap.artifact_type,
  ap.num_shared_artifacts,
  CASE
    WHEN ap.oso_project_id = ch.best_oso_project_id THEN TRUE
    ELSE FALSE
  END AS is_best_match
FROM all_pairs AS ap
LEFT JOIN chosen AS ch
  ON ap.gitcoin_project_id = ch.gitcoin_project_id