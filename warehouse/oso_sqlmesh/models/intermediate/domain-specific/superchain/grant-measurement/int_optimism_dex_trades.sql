MODEL (
  name oso.int_optimism_dex_trades,
  description 'DEX trade events on OP Mainnet',
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
  grain (bucket_day, project_name, dex_address, count, l2_gas_fee, from_artifact_id),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := bucket_day,
      no_gap_date_part := 'month',
    ),
  )
);

WITH dexs AS (
 SELECT
    artifact_id,
    project_name,
    artifact_name AS dex_address
FROM oso.int_artifacts_by_project_in_openlabelsinitiative
WHERE
    artifact_source = 'OPTIMISM'
    AND usage_category = 'dex'
	AND project_name != 'unknown'
)

SELECT
  txs.bucket_day,
  d.project_name,
  d.dex_address,
  txs.count,
  txs.l2_gas_fee,
  txs.from_artifact_id
FROM oso.int_events_daily__l2_transactions AS txs
JOIN dexs AS d
  ON txs.from_artifact_id = d.artifact_id
WHERE
  txs.event_source = 'OPTIMISM'
  AND txs.event_type = 'TRANSACTION'
  AND txs.bucket_day BETWEEN @start_dt AND @end_dt