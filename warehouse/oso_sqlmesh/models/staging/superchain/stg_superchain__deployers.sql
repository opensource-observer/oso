model(
    name oso.stg_superchain__deployers,
    kind incremental_by_time_range(
        time_column block_timestamp, batch_size 180, batch_concurrency 1, lookback 7
    ),
    start '2021-10-01',
    cron '@daily',
    partitioned_by(day("block_timestamp"), "chain"),
    grain(
        block_timestamp, chain_id, transaction_hash, deployer_address, contract_address
    )
)
;

@transactions_with_receipts_deployers(
    @start_dt,
    @end_dt,
    @oso_source('bigquery.optimism_superchain_raw_onchain_data.transactions'),
    transactions.chain as chain,
    block_timestamp_column := @from_unix_timestamp(transactions.block_timestamp),
    time_partition_column := transactions.dt,
)
