from ..factories.goldsky import (
    goldsky_asset,
    traces_checks,
    transactions_checks,
    blocks_checks,
)

zora_blocks = goldsky_asset(
    key_prefix="zora",
    name="blocks",
    source_name="zora-blocks",
    project_id="opensource-observer",
    destination_table_name="zora_blocks",
    working_destination_dataset_name="oso_raw_sources",
    destination_dataset_name="superchain",
    partition_column_name="timestamp",
    partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
    checks=[blocks_checks()],
    # uncomment the following value to test
    # max_objects_to_load=1,
)

zora_transactions = goldsky_asset(
    key_prefix="zora",
    name="transactions",
    source_name="zora-enriched_transactions",
    project_id="opensource-observer",
    destination_table_name="zora_transactions",
    working_destination_dataset_name="oso_raw_sources",
    destination_dataset_name="superchain",
    partition_column_name="block_timestamp",
    partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
    schema_overrides=[{"name": "value", "field_type": "BYTES"}],
    checks=[transactions_checks("opensource-observer.superchain.zora_blocks")],
    # uncomment the following value to test
    # max_objects_to_load=1,
    deps=zora_blocks.assets,
)

zora_traces = goldsky_asset(
    key_prefix="zora",
    name="traces",
    source_name="zora-traces",
    project_id="opensource-observer",
    destination_table_name="zora_traces",
    working_destination_dataset_name="oso_raw_sources",
    destination_dataset_name="superchain",
    partition_column_name="block_timestamp",
    partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
    checks=[traces_checks("opensource-observer.superchain.zora_transactions")],
    # uncomment the following value to test
    # max_objects_to_load=1,
    deps=zora_transactions.assets,
)
