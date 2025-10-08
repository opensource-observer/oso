MODEL (
  name oso.int_optimism_static_calls_to_oracles_daily_by_project,
  description "Optimism static calls to oracles daily by project",
  dialect trino,
  kind incremental_by_time_range(
   time_column bucket_day,
   batch_size 60,
   batch_concurrency 2,
   lookback 31,
   forward_only true,
   on_destructive_change warn,
  ),
  start '2024-09-01',
  cron '@daily',
  partitioned_by MONTH("bucket_day"),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := bucket_day,
      no_gap_date_part := 'day',
      ignore_before := @superchain_audit_start,
      ignore_after := @superchain_audit_end,
      missing_rate_min_threshold := 0.95,
    ),
  ),
);

WITH apps AS (
  SELECT DISTINCT
    artifact_id,
    project_name AS app_name
  FROM oso.artifacts_by_project_v1
  WHERE
    project_source = 'OSS_DIRECTORY'
    AND project_namespace = 'oso'
    AND artifact_source = 'OPTIMISM'
)

SELECT
  sc.bucket_day,
  sc.project_name AS oracle_name,
  to_apps.app_name AS to_project_name,
  from_apps.app_name AS from_project_name,
  sc.from_address_trace,
  sc.to_address_trace,
  sc.to_address_tx,
  sc.read_op_fees_gwei,
  sc.amortized_read_op_fees_gwei,
  sc.l2_tx_fees_gwei,
  sc.l1_fees_gwei,
  sc.amortized_l1_fees_gwei,
  sc.transaction_count
FROM oso.int_optimism_static_calls_to_oracles_daily AS sc
LEFT JOIN apps AS to_apps
  ON to_apps.artifact_id = sc.to_artifact_id
LEFT JOIN apps AS from_apps
  ON from_apps.artifact_id = sc.from_artifact_id
WHERE
  sc.bucket_day BETWEEN @start_dt AND @end_dt
  AND sc.project_name != from_apps.app_name