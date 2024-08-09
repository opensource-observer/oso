from ..factories.goldsky import goldsky_network_assets


mode_network = goldsky_network_assets(
    network_name="mode",
    destination_dataset_name="superchain",
    working_destination_dataset_name="oso_raw_sources",
    transactions_config={"source_name": "mode-receipt_transactions"},
)
