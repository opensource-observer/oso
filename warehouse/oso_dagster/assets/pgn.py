from ..factories.goldsky import goldsky_network_assets

# pgn_blocks = goldsky_asset(
#     key_prefix="pgn",
#     name="blocks",
#     source_name="pgn-blocks",
#     project_id="opensource-observer",
#     destination_table_name="pgn_blocks",
#     working_destination_dataset_name="oso_raw_sources",
#     destination_dataset_name="superchain",
#     partition_column_name="timestamp",
#     partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
#     checks=[blocks_checks()],
# )

# pgn_transactions = goldsky_asset(
#     key_prefix="pgn",
#     name="transactions",
#     source_name="pgn-enriched_transactions",
#     project_id="opensource-observer",
#     destination_table_name="pgn_transactions",
#     working_destination_dataset_name="oso_raw_sources",
#     destination_dataset_name="superchain",
#     partition_column_name="block_timestamp",
#     partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
#     schema_overrides=[{"name": "value", "field_type": "BYTES"}],
#     checks=[transactions_checks("opensource-observer.superchain.pgn_blocks")],
#     deps=pgn_blocks.assets,
# )

# pgn_traces = goldsky_asset(
#     key_prefix="pgn",
#     name="traces",
#     source_name="pgn-traces",
#     project_id="opensource-observer",
#     destination_table_name="pgn_traces",
#     working_destination_dataset_name="oso_raw_sources",
#     destination_dataset_name="superchain",
#     partition_column_name="block_timestamp",
#     partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
#     checks=[traces_checks("opensource-observer.superchain.pgn_transactions")],
#     deps=pgn_transactions.assets,
# )

pgn_network = goldsky_network_assets(
    network_name="pgn",
    destination_dataset_name="superchain",
    working_destination_dataset_name="oso_raw_sources",
)
