from ..factories.goldsky import goldsky_network_assets

frax_network = goldsky_network_assets(
    network_name="frax",
    destination_dataset_name="superchain",
    working_destination_dataset_name="oso_raw_sources",
    transactions_config={"source_name": "frax-receipt_transactions"},
)
