model(
    name oso.stg_superchain__potential_bots,
    kind full,
    start @blockchain_incremental_start,
    cron '@daily',
    partitioned_by(day("min_block_time"), "chain_name"),
    grain(chain_name, address),
    enabled false,
    audits (
      has_at_least_n_rows(threshold := 0)
    )
)
;

@potential_bots(
    @oso_source('bigquery.optimism_superchain_raw_onchain_data.transactions'),
    chain_name_column := @chain_name(transactions.chain),
    block_timestamp_column := @from_unix_timestamp(transactions.block_timestamp),
    time_partition_column := transactions.dt,
)
