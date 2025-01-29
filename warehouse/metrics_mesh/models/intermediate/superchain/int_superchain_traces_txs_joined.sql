MODEL (
  name metrics.int_superchain_traces_txs_joined,
  description 'Traces joined on transactions',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (
    block_timestamp,
    chain,
    transaction_hash,
    from_address_tx,
    to_address_tx,
    from_address_trace,
    to_address_trace
  )
);

select
  transactions.block_timestamp,
  transactions.transaction_hash,
  transactions.chain,
  transactions.from_address as from_address_tx,
  traces.from_address as from_address_trace,
  traces.to_address as to_address_trace,
  transactions.to_address as to_address_tx,
  transactions.gas_used as gas_used_tx,
  traces.gas_used as gas_used_trace,
  transactions.gas_price as gas_price_tx
from metrics.stg_superchain__transactions as transactions
left join metrics.stg_superchain__traces as traces
  on transactions.transaction_hash = traces.transaction_hash