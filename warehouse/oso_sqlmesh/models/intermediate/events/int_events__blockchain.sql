-- Blockchain events (currently only from the superchain dataset)
MODEL (
  name oso.int_events__blockchain,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 180,
    batch_concurrency 1
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by (DAY("time"), "event_type", "event_source"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id)
);

WITH events AS (
  SELECT
    block_timestamp,
    chain,
    transaction_hash,
    from_address_tx AS from_address,
    CASE 
      WHEN to_address_trace != to_address_tx THEN to_address_trace
      ELSE to_address_tx
    END as to_address,
    CASE 
      WHEN to_address_trace != to_address_tx THEN 'CONTRACT_INTERNAL_INVOCATION'
      ELSE 'CONTRACT_INVOCATION'
    END AS event_type,
    CASE 
      WHEN to_address_trace != to_address_tx THEN gas_used_trace
      ELSE gas_used_tx
    END AS gas_used,
    gas_price_tx
  FROM oso.int_superchain_traces_txs_joined
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
  gas_used,
  gas_price_tx,
  transaction_hash
FROM events
