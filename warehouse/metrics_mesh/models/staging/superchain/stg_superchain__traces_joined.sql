MODEL (
  name metrics.stg_superchain__traces_joined,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "event_source"),
  grain (block_timestamp, event_source, transaction_hash, from_address_tx, from_address_trace, to_address_trace, to_address_tx)
);

select
  transactions.block_timestamp,
  transactions.transaction_hash,
  transactions.from_address as from_address_tx,
  traces.from_address as from_address_trace,
  traces.to_address as to_address_trace,
  transactions.to_address as to_address_tx,
  transactions.gas as gas,
  traces.gas_used as gas_used_trace,
  transactions.gas_price as gas_price,
  upper(
    case
      when transactions.chain = 'op' then 'optimism'
      when transactions.chain = 'fraxtal' then 'frax'
      else transactions.chain
    end
  ) as event_source
from @oso_source('bigquery.optimism_superchain_raw_onchain_data.transactions') as transactions
left join @oso_source('bigquery.optimism_superchain_raw_onchain_data.traces') as traces
  on transactions.transaction_hash = traces.transaction_hash
  and transactions.chain = traces.chain