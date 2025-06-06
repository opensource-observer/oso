MODEL (
  name oso.int_deployers,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 365,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
    on_destructive_change warn,
  ),
  start @blockchain_incremental_start,
  partitioned_by (DAY("block_timestamp"), "chain"),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := block_timestamp,
      no_gap_date_part := 'day',
      ignore_before := @superchain_audit_start,
      ignore_after := @superchain_audit_end,
      missing_rate_min_threshold := 0.95,
    ),
  ),
  tags (
    "incremental"
  )
);

SELECT
  block_timestamp,
  transaction_hash,
  deployer_address,
  contract_address,
  UPPER(chain) AS chain
FROM oso.stg_superchain__deployers