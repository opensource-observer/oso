-- Blockchain events (currently only from the superchain dataset)
MODEL (
  name oso.int_events__blockchain,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 180,
    batch_concurrency 1
  ),
  start '2021-10-01',
  cron '@daily',
  partitioned_by (DAY("time"), "event_type", "event_source"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id)
);

@DEF(to_artifact_id, @oso_id(traces_txs.chain, traces_txs.to_address_trace))
@DEF(from_artifact_id, @oso_id(traces_txs.chain, traces_txs.from_address_trace))

SELECT
  time,
  to_artifact_id,
  from_artifact_id,
  'CONTRACT_INVOCATION' AS event_type,
  @oso_id(traces_txs.transaction_hash, traces_txs.to_address_trace) AS event_source_id,
  UPPER(traces_txs.chain) AS event_source,
  @oso_id(traces_txs.chain, traces_txs.to_address_trace) AS to_artifact_id,
  LOWER(traces_txs.to_address_trace) AS to_artifact_name,
  LOWER(traces_txs.chain) AS to_artifact_namespace,
  UPPER('CONTRACT') AS to_artifact_type,
  LOWER(traces_txs.from_address_trace) AS to_artifact_source_id,
  @oso_id(traces_txs.chain, traces_txs.from_address_trace) AS from_artifact_id,
  LOWER(traces_txs.from_address_trace) AS from_artifact_name,
  LOWER(traces_txs.chain) AS from_artifact_namespace,
  -- The exact categorization of an address can't be known in the event table.
  -- We can only know if it's a contract or an EOA.
  UPPER(CASE WHEN 
    traces_txs.to_address_trace = traces.to_address_tx THEN 'EOA' 
    ELSE 'CONTRACT' 
  END) AS from_artifact_type,
  LOWER(traces_txs.from_address_trace) AS from_artifact_source_id,
  (traces_txs.gas_used_tx * traces_txs.gas_price_tx)::DOUBLE AS amount
  traces_txs.transaction_hash as transaction_hash,
  traces_txs.gas_price As gas_price,
  traces_txs.gas_used_tx AS gas_used_tx,
  traces_txs.gas_used_trace as gas_used_trace,
FROM oso.int_superchain_traces_txs_joined as traces_txs
WHERE
  traces_txs.block_timestamp BETWEEN @start_dt AND @end_dt