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

@DEF(half_life_days, 365.0);

WITH last_date AS (
  SELECT MAX(bucket_day) AS last_bucket
  FROM oso.int_events_daily__github
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
    e.from_artifact_id AS dev_artifact_id,
    u.artifact_name AS dev_name,
    e.to_artifact_id AS repo_artifact_id,
    sum(
      coalesce(w.w,1.0)
      * coalesce(e.amount,1.0)
      * exp(
        - (ln(2) / @half_life_days)
        * CAST(date_diff('day', e.bucket_day, ld.last_bucket) AS DOUBLE)
      )
    ) AS edge_weight,
    count(*) AS event_count
  FROM oso.int_events_daily__github AS e
  JOIN oso.int_github_users_bot_filtered AS u
    ON e.from_artifact_id = u.artifact_id
  LEFT JOIN event_weights AS w
    ON e.event_type = w.event_type
  CROSS JOIN last_date AS ld
  WHERE NOT u.is_bot
    AND e.event_type IN (
      'STARRED',
      'FORKED',
      'ISSUE_OPENED',
      'PULL_REQUEST_OPENED',
      'COMMIT_CODE'
    )
  GROUP BY
    e.from_artifact_id,
    u.artifact_name,
    e.to_artifact_id
)

SELECT
  e.dev_artifact_id,
  e.dev_name,
  e.repo_artifact_id,
  r.artifact_url AS url,
  e.edge_weight,
  e.event_count
FROM dev_repo_edges AS e
JOIN oso.int_artifacts__github AS r