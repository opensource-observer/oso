from ..factories.goldsky import goldsky_network_assets

# base_blocks = goldsky_asset(
#     key_prefix="base",
#     name="blocks",
#     source_name="base-blocks",
#     project_id="opensource-observer",
#     destination_table_name="base_blocks",
#     working_destination_dataset_name="oso_raw_sources",
#     destination_dataset_name="superchain",
#     partition_column_name="timestamp",
#     partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
#     checks=[blocks_checks()],
#     additional_jobs=[blocks_additional_jobs()],
# )

# base_transactions = goldsky_asset(
#     key_prefix="base",
#     name="transactions",
#     source_name="base-enriched_transactions",
#     project_id="opensource-observer",
#     destination_table_name="base_transactions",
#     working_destination_dataset_name="oso_raw_sources",
#     destination_dataset_name="superchain",
#     partition_column_name="block_timestamp",
#     partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
#     schema_overrides=[{"name": "value", "field_type": "BYTES"}],
#     checks=[transactions_checks("opensource-observer.superchain.base_blocks")],
#     deps=base_blocks.assets,
#     additional_jobs=[
#         transactions_additional_jobs(
#             blocks_table_fqn="opensource-observer.superchain.base_blocks"
#         )
#     ],
# )

# base_traces = goldsky_asset(
#     key_prefix="base",
#     name="traces",
#     source_name="base-traces",
#     project_id="opensource-observer",
#     destination_table_name="base_traces",
#     working_destination_dataset_name="oso_raw_sources",
#     destination_dataset_name="superchain",
#     partition_column_name="block_timestamp",
#     partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
#     checks=[traces_checks("opensource-observer.superchain.base_transactions")],
#     deps=base_transactions.assets,
#     additional_jobs=[
#         traces_additional_jobs(
#             transactions_table_fqn="opensource-observer.superchain.base_transactions"
#         )
#     ],
# )


base_network = goldsky_network_assets(
    network_name="base",
    destination_dataset_name="superchain",
    working_destination_dataset_name="oso_raw_sources",
)
