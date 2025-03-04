model(
    name oso.stg_superchain__traces,
    kind incremental_by_time_range(
        time_column block_timestamp, batch_size 180, batch_concurrency 1, lookback 7
    ),
    start '2021-10-01',
    cron '@daily',
    partitioned_by(day("block_timestamp"), "chain"),
    grain(block_timestamp, chain, transaction_hash, from_address, to_address)
)
;

select
    @from_unix_timestamp(block_timestamp) as block_timestamp,
    transaction_hash,
    from_address,
    to_address,
    gas_used,
    @chain_name(chain) as chain
from @oso_source('bigquery.optimism_superchain_raw_onchain_data.traces')
where
    network = 'mainnet'
    and "status" = 1
    and call_type in ('delegatecall', 'call')
    and gas_used > 0
    -- Bigquery requires we specify partitions to filter for this data source
    and dt between @start_dt and @end_dt
