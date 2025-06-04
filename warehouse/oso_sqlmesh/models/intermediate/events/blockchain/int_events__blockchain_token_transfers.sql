MODEL (
  name oso.int_events__blockchain_token_transfers,
  description "Intermediate table for blockchain token transfers",
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 180,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
    on_destructive_change warn,
  ),
  start @blockchain_incremental_start,
  cron '@weekly',
  partitioned_by (DAY("time"), "event_type", "event_source"),
  grain (time, from_artifact_id, to_artifact_id, event_source_id),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := time,
      no_gap_date_part := 'day',
      ignore_before := @superchain_audit_start,
      ignore_after := @superchain_audit_end,
      missing_rate_min_threshold := 0.95,
    ),
  ),
  tags (
    "blockchain",
    "superchain",
    "incremental",
  ),
);

SELECT
  block_timestamp AS time,
  @oso_entity_id(chain, '', to_address) AS to_artifact_id,
  @oso_entity_id(chain, '', from_address) AS from_artifact_id,
  'BLOCKCHAIN_TOKEN_TRANSFER' AS event_type,
  -- TODO: refactor to ensure unique event_source_id
  @oso_id(chain, '', transaction_hash) AS event_source_id,
  chain AS event_source,
  '' AS to_artifact_namespace,
  to_address AS to_artifact_name,
  to_address AS to_artifact_source_id,
  '' AS from_artifact_namespace,
  from_address AS from_artifact_name,
  from_address AS from_artifact_source_id,
  value_lossless::DOUBLE AS amount
FROM oso.stg_superchain__transactions
WHERE
  value_lossless::DOUBLE > 0
  AND block_timestamp BETWEEN @start_dt AND @end_dt
