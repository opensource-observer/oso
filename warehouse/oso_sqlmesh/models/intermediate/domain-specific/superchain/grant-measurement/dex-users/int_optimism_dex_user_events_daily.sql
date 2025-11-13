MODEL (
  name oso.int_optimism_dex_user_events_daily,
  description 'DEX user events on OP Mainnet by day',
  dialect trino,
  kind incremental_by_time_range(
    time_column bucket_day,
    batch_size 12,
    batch_concurrency 2,
    forward_only true,
    lookback @default_daily_incremental_lookback,
    auto_restatement_cron @default_auto_restatement_cron
  ),
  start @blockchain_incremental_start,
  cron '@monthly',
  partitioned_by MONTH("bucket_day"),
  grain (bucket_day, user_address, dex_address, dex_project_name),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := bucket_day,
      no_gap_date_part := 'day',
    ),
  )
);

WITH dexs AS (
 SELECT
    artifact_id,
    project_name AS dex_project_name,
    artifact_name AS dex_address
FROM oso.int_artifacts_by_project_in_openlabelsinitiative
WHERE
    artifact_source = 'OPTIMISM'
    AND usage_category = 'dex'
	AND project_name != 'unknown'
)


SELECT
  DATE_TRUNC('DAY', tx.time::DATE) AS bucket_day,
  tx.from_artifact_name AS user_address,
  dexs.dex_address,
  dexs.dex_project_name,
  SUM(tx.l2_gas_fee / 1e18)::DOUBLE AS total_gas_fees,
  COUNT(*) AS total_transactions
FROM oso.int_events__superchain_transactions AS tx
LEFT JOIN dexs ON tx.to_artifact_id = dexs.artifact_id
WHERE
  tx.event_source = 'OPTIMISM'
  AND tx.event_type = 'TRANSACTION'
  AND tx.time BETWEEN @start_dt AND @end_dt
GROUP BY 1, 2, 3, 4