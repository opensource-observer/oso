from ..factories.goldsky import goldsky_asset, traces_checks

optimism_traces = goldsky_asset(
    key_prefix="optimism",
    name="traces",
    source_name="optimism-traces",
    project_id="opensource-observer",
    destination_table_name="optimism_traces",
    working_destination_dataset_name="oso_raw_sources",
    destination_dataset_name="superchain",
    partition_column_name="block_timestamp",
    dedupe_model="optimism_dedupe.sql",
    checks=[
        traces_checks(
            "bigquery-public-data.goog_blockchain_optimism_mainnet_us.transactions",
            transactions_transaction_hash_column_name="transaction_hash",
        )
    ],
    # uncomment the following value to test
    # max_objects_to_load=2000,
)
