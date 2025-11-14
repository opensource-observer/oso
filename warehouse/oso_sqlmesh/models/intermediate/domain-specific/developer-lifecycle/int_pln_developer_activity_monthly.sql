MODEL (
  name oso.int_pln_developer_activity_monthly,
  description 'Developer activity to projects in the Protocol Labs Network, aggregated by month',
  dialect trino,
  kind incremental_by_time_range(
    time_column bucket_month,
    batch_size 12,
    batch_concurrency 2,
    forward_only true,
    lookback @default_daily_incremental_lookback,
    auto_restatement_cron @default_auto_restatement_cron
  ),
  start @github_incremental_start,
  cron '@monthly',
  partitioned_by MONTH("bucket_month"),
  grain (bucket_month, from_artifact_id, to_project_id),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := bucket_month,
      no_gap_date_part := 'month',
    ),
  ),
  tags (
    'entity_category=project',
    'entity_category=collection',
  )
);

SELECT
  DATE_TRUNC('MONTH', e.bucket_day::DATE) AS bucket_month,
  e.from_artifact_id,
  abp.project_id AS to_project_id,
  COUNT(DISTINCT e.bucket_day) AS days_active
FROM oso.int_events_daily__github AS e
JOIN oso.artifacts_by_project_v1 AS abp
  ON e.to_artifact_id = abp.artifact_id
JOIN oso.projects_by_collection_v1 AS pbc
  ON abp.project_id = pbc.project_id
WHERE
  abp.artifact_source = 'GITHUB'
  AND pbc.collection_name = 'protocol-labs-network'
  AND e.event_type IN (
    'COMMIT_CODE',
    'ISSUE_CLOSED',
    'ISSUE_COMMENT',    
    'ISSUE_OPENED',
    'ISSUE_REOPENED',
    'PULL_REQUEST_CLOSED',
    'PULL_REQUEST_MERGED',
    'PULL_REQUEST_OPENED',
    'PULL_REQUEST_REVIEW_COMMENT',
    'PULL_REQUEST_REOPENED',
  )
  AND e.bucket_day BETWEEN @start_dt AND @end_dt
GROUP BY 1, 2, 3