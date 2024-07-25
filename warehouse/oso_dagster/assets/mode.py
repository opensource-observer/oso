from ..factories.goldsky import goldsky_network_assets

# mode_blocks = goldsky_asset(
#     key_prefix="mode",
#     name="blocks",
#     source_name="mode-blocks",
#     project_id="opensource-observer",
#     destination_table_name="mode_blocks",
#     working_destination_dataset_name="oso_raw_sources",
#     destination_dataset_name="superchain",
#     partition_column_name="timestamp",
#     partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
#     checks=[blocks_checks()],
# )

# mode_transactions = goldsky_asset(
#     key_prefix="mode",
#     name="transactions",
#     source_name="mode-receipt_transactions",
#     project_id="opensource-observer",
#     destination_table_name="mode_transactions",
#     working_destination_dataset_name="oso_raw_sources",
#     destination_dataset_name="superchain",
#     partition_column_name="block_timestamp",
#     partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
#     schema_overrides=[{"name": "value", "field_type": "BYTES"}],
#     checks=[transactions_checks("opensource-observer.superchain.mode_blocks")],
#     # uncomment the following value to test
#     # max_objects_to_load=1,
#     deps=mode_blocks.assets,
# )

# mode_traces = goldsky_asset(
#     key_prefix="mode",
#     name="traces",
#     source_name="mode-traces",
#     project_id="opensource-observer",
#     destination_table_name="mode_traces",
#     working_destination_dataset_name="oso_raw_sources",
#     destination_dataset_name="superchain",
#     partition_column_name="block_timestamp",
#     partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
#     checks=[traces_checks("opensource-observer.superchain.mode_transactions")],
#     # uncomment the following value to test
#     # max_objects_to_load=1,
#     deps=mode_transactions.assets,
# )

mode_network = goldsky_network_assets(
    network_name="mode",
    destination_dataset_name="superchain",
    working_destination_dataset_name="oso_raw_sources",
    transactions_config={"source_name": "mode-receipt_transactions"},
)
