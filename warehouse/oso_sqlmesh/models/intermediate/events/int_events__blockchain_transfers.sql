-- Blockchain events (currently only from the superchain dataset)
MODEL (
  name oso.int_events__blockchain_transfers,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 180,
    batch_concurrency 1
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  dialect trino,
  partitioned_by (DAY("time"), "event_type", "event_source"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH txns AS (
  SELECT
    transaction_hash,
    block_timestamp,
    chain,
    from_address,
    to_address,
    value_lossless::DOUBLE AS amount,
    'BLOCKCHAIN_TRANSFER' AS event_type
  FROM oso.stg_superchain__transactions
  WHERE block_timestamp BETWEEN @start_dt AND @end_dt
)

SELECT
  block_timestamp AS time,
  @oso_entity_id(chain, '', to_address) AS to_artifact_id,
  @oso_entity_id(chain, '', from_address) AS from_artifact_id,
  event_type,
  -- TODO: refactor to ensure unique event_source_id
  @oso_id(chain, '', transaction_hash) AS event_source_id,
  chain AS event_source,
  '' AS to_artifact_namespace,
  to_address AS to_artifact_name,
  to_address AS to_artifact_source_id,
  '' AS from_artifact_namespace,
  from_address AS from_artifact_name,
  from_address AS from_artifact_source_id,
  amount
FROM txns
WHERE amount > 0