MODEL (
  name oso.int_ddp_repo_to_dev_graph,
  description "Graph of repositories to developers",
  kind FULL,
  dialect trino,
  grain (dev_artifact_id, dev_name, repo_artifact_id, edge_weight, event_count),
  tags (
    'entity_category=artifact'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

@DEF(half_life_months, 12);

WITH last_date AS (
  SELECT MAX(bucket_month) AS last_bucket
  FROM oso.int_ddp_filtered_github_events_by_month
),
event_weights AS (
  SELECT 'STARRED' event_type,1.0 w UNION ALL
  SELECT 'FORKED',1.5 UNION ALL
  SELECT 'ISSUE_OPENED',0.5 UNION ALL
  SELECT 'PULL_REQUEST_OPENED',2.0 UNION ALL
  SELECT 'COMMIT_CODE',2.5
),
dev_repo_edges AS (
  SELECT
    e.git_user,
    e.repo_artifact_id,
    SUM(
      coalesce(w.w,1.0)
      * coalesce(e.amount,1.0)
      * exp(
          - (ln(2) / CAST(@half_life_months AS DOUBLE))
          * CAST(date_diff('MONTH', e.bucket_month, ld.last_bucket) AS DOUBLE)
        )
    ) AS edge_weight,
    COUNT(*) AS event_count
  FROM oso.int_ddp_filtered_github_events_by_month AS e
  LEFT JOIN event_weights AS w
    ON e.event_type = w.event_type
  CROSS JOIN last_date AS ld
  GROUP BY 1,2
)

SELECT
  d.git_user,
  d.repo_artifact_id,
  a.artifact_url AS url,
  d.edge_weight,
  d.event_count
FROM dev_repo_edges AS d
JOIN oso.int_artifacts__github AS a
  ON d.repo_artifact_id = a.artifact_id
ORDER BY d.edge_weight DESC