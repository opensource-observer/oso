MODEL (
  name oso.int_ddp_repo_metrics_pivoted,
  description "Pivoted metrics for Developer Data Program repositories",
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

SELECT
  artifact_id,
  MAX(
    CASE WHEN metric_model = 'contributors' THEN metric_amount ELSE 0 END
  ) AS contributor_count,
  MAX(
    CASE WHEN metric_model = 'commits' THEN metric_amount ELSE 0 END
  ) AS commit_count,
  MAX(
    CASE WHEN metric_model = 'forks' THEN metric_amount ELSE 0 END
  ) AS fork_count,
  MAX(
    CASE WHEN metric_model = 'stars' THEN metric_amount ELSE 0 END
  ) AS star_count,
  MAX(
    CASE WHEN metric_model = 'opened_issues' THEN metric_amount ELSE 0 END
  ) AS opened_issue_count,
  MAX(
    CASE WHEN metric_model = 'closed_issues' THEN metric_amount ELSE 0 END
  ) AS closed_issue_count,
  MAX(
    CASE WHEN metric_model = 'opened_pull_requests' THEN metric_amount ELSE 0 END
  ) AS opened_pull_request_count,
  MAX(
    CASE WHEN metric_model = 'merged_pull_requests' THEN metric_amount ELSE 0 END
  ) AS merged_pull_request_count,
  MAX(
    CASE WHEN metric_model = 'releases' THEN metric_amount ELSE 0 END
  ) AS release_count,
  MAX(
    CASE WHEN metric_model = 'comments' THEN metric_amount ELSE 0 END
  ) AS comment_count
FROM oso.int_ddp_repo_metrics
GROUP BY artifact_id