MODEL (
  name oso.int_ddp_repo_discovery_v0,
  description "v0 discovery algorithm for finding related repositories to Ethereum development",
  kind FULL,
  dialect trino,
  tags (
    'entity_category=artifact',
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

@DEF(alpha, 0.5);
@DEF(num_iterations, 2);

-- 1. base repo scores
WITH repo_base AS (
  SELECT
    repo_artifact_id,
    score AS repo_score_base
  FROM oso.int_ddp_repo_pretrust
),
-- 2. edges (already aggregated and decayed by month)
edges_raw AS (
  SELECT
    git_user,
    repo_artifact_id,
    edge_weight
  FROM oso.int_ddp_repo_to_dev_graph
),
-- 3. normalize outgoing edges per developer 
edges_norm AS (
  SELECT
    git_user,
    repo_artifact_id,
    edge_weight,
    edge_weight / NULLIF(sum(edge_weight) OVER (PARTITION BY git_user),0) AS edge_weight_norm
  FROM edges_raw
),
-- 4. developer trust v1 = weighted average of base repo scores they touched
dev_trust_v1 AS (
  SELECT
    e.git_user,
    COALESCE(sum(e.edge_weight_norm * r.repo_score_base),0.0) AS dev_score_v1
  FROM edges_norm AS e
  LEFT JOIN repo_base AS r
    ON e.repo_artifact_id = r.repo_artifact_id
  GROUP BY 1
),
-- 5. repo contribution from developers (pull dev trust back to repos using same normalized edges)
repo_from_dev_v1 AS (
  SELECT
    e.repo_artifact_id,
    sum(e.edge_weight_norm * d.dev_score_v1) AS repo_dev_contrib_v1
  FROM edges_norm AS e
  LEFT JOIN dev_trust_v1 d
    ON e.git_user = d.git_user
  GROUP BY 1
),
-- 6. mix base score and dev contrib using alpha to get repo_score_v1
repo_score_v1 AS (
  SELECT
    r.repo_artifact_id,
    r.repo_score_base,
    COALESCE(c.repo_dev_contrib_v1,0.0) AS repo_dev_contrib_v1,
    ( @alpha * r.repo_score_base )
      + ( (1 - @alpha) * COALESCE(c.repo_dev_contrib_v1,0.0) ) AS repo_score_v1
  FROM repo_base AS r
  LEFT JOIN repo_from_dev_v1 AS c
    ON r.repo_artifact_id = c.repo_artifact_id
),
-- 7. second iteration: recompute dev trust from repo_score_v1
dev_trust_v2 AS (
  SELECT
    e.git_user,
    COALESCE(sum(e.edge_weight_norm * r.repo_score_v1),0.0) AS dev_score_v2
  FROM edges_norm e
  LEFT JOIN repo_score_v1 r ON e.repo_artifact_id = r.repo_artifact_id
  GROUP BY 1
),
repo_from_dev_v2 AS (
  SELECT
    e.repo_artifact_id,
    sum(e.edge_weight_norm * d.dev_score_v2) AS repo_dev_contrib_v2
  FROM edges_norm e
  LEFT JOIN dev_trust_v2 d ON e.git_user = d.git_user
  GROUP BY 1
),
repo_score_v2 AS (
  SELECT
    r.repo_artifact_id,
    r.repo_score_base,
    COALESCE(v1.repo_dev_contrib_v1,0.0) AS repo_dev_contrib_v1,
    COALESCE(v2.repo_dev_contrib_v2,0.0) AS repo_dev_contrib_v2,
    ( @alpha * r.repo_score_base )
      + ( (1 - @alpha) * COALESCE(v2.repo_dev_contrib_v2, v1.repo_dev_contrib_v1, 0.0) ) AS repo_score_final
  FROM repo_base AS r
  LEFT JOIN repo_from_dev_v1 AS v1
    ON r.repo_artifact_id = v1.repo_artifact_id
  LEFT JOIN repo_from_dev_v2 AS v2
    ON r.repo_artifact_id = v2.repo_artifact_id
)
-- 8. output: ranked repos with diagnostics
SELECT
  r.repo_artifact_id,
  a.artifact_url AS url,
  r.repo_score_base AS base_score,
  r.repo_dev_contrib_v1 AS dev_contrib_v1,
  r.repo_dev_contrib_v2 AS dev_contrib_v2,
  r.repo_score_final AS final_score,
  r.repo_score_final - r.repo_score_base AS delta_score,
  rank() OVER (ORDER BY r.repo_score_final DESC) AS trust_rank
FROM repo_score_v2 r
LEFT JOIN oso.int_artifacts__github AS a
  ON r.repo_artifact_id = a.artifact_id
ORDER BY final_score DESC