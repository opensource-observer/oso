model(
    name oso.stg_superchain__first_time_addresses,
    kind incremental_by_time_range(
        time_column first_block_timestamp,
        batch_size 180,
        batch_concurrency 1,
        lookback 7
    ),
    start '2021-10-01',
    cron '@daily',
    partitioned_by(day("first_block_timestamp"), "chain_name"),
    grain(
        address,
        chain_name,
        first_block_timestamp,
        first_tx_to,
        first_tx_hash,
        first_method_id
    ),
    enabled false,
)
;

@first_time_addresses(
    @start_dt,
    @end_dt,
    @oso_source('bigquery.optimism_superchain_raw_onchain_data.transactions'),
    chain_name_column := transactions.chain,
    block_timestamp_column := @from_unix_timestamp(transactions.block_timestamp),
    time_partition_column := transactions.dt,
)
