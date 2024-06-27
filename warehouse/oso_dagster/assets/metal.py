from ..factories.goldsky import (
    goldsky_asset,
    traces_checks,
    transactions_checks,
    blocks_checks,
)

metal_blocks = goldsky_asset(
    key_prefix="metal",
    name="blocks",
    source_name="metal-blocks",
    project_id="opensource-observer",
    destination_table_name="metal_blocks",
    working_destination_dataset_name="oso_raw_sources",
    destination_dataset_name="superchain",
    partition_column_name="timestamp",
    partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
    checks=[blocks_checks()],
)

metal_transactions = goldsky_asset(
    key_prefix="metal",
    name="transactions",
    source_name="metal-receipt_transactions",
    project_id="opensource-observer",
    destination_table_name="metal_transactions",
    working_destination_dataset_name="oso_raw_sources",
    destination_dataset_name="superchain",
    partition_column_name="block_timestamp",
    partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
    schema_overrides=[{"name": "value", "field_type": "BYTES"}],
    checks=[transactions_checks("opensource-observer.superchain.metal_blocks")],
    deps=metal_blocks.assets,
)


metal_traces = goldsky_asset(
    key_prefix="metal",
    name="traces",
    source_name="metal-traces",
    project_id="opensource-observer",
    destination_table_name="metal_traces",
    working_destination_dataset_name="oso_raw_sources",
    destination_dataset_name="superchain",
    partition_column_name="block_timestamp",
    partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
    checks=[traces_checks("opensource-observer.superchain.metal_transactions")],
    deps=metal_transactions.assets,
)
