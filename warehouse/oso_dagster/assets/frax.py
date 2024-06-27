from ..factories.goldsky import (
    goldsky_asset,
    traces_checks,
    transactions_checks,
    blocks_checks,
)

frax_blocks = goldsky_asset(
    key_prefix="frax",
    name="blocks",
    source_name="frax-blocks",
    project_id="opensource-observer",
    destination_table_name="frax_blocks",
    working_destination_dataset_name="oso_raw_sources",
    destination_dataset_name="superchain",
    partition_column_name="timestamp",
    partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
    checks=[blocks_checks()],
    # uncomment the following value to test
    # max_objects_to_load=1,
)

frax_transactions = goldsky_asset(
    key_prefix="frax",
    name="transactions",
    source_name="frax-receipt_transactions",
    project_id="opensource-observer",
    destination_table_name="frax_transactions",
    working_destination_dataset_name="oso_raw_sources",
    destination_dataset_name="superchain",
    partition_column_name="block_timestamp",
    partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
    schema_overrides=[{"name": "value", "field_type": "BYTES"}],
    checks=[transactions_checks("opensource-observer.superchain.frax_blocks")],
    # uncomment the following value to test
    # max_objects_to_load=1,
    deps=frax_blocks.assets,
)

frax_traces = goldsky_asset(
    key_prefix="frax",
    name="traces",
    source_name="frax-traces",
    project_id="opensource-observer",
    destination_table_name="frax_traces",
    working_destination_dataset_name="oso_raw_sources",
    destination_dataset_name="superchain",
    partition_column_name="block_timestamp",
    partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
    checks=[traces_checks("opensource-observer.superchain.frax_transactions")],
    # uncomment the following value to test
    # max_objects_to_load=1,
    deps=frax_transactions.assets,
)
