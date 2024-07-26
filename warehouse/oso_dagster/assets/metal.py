from ..factories.goldsky import (
    goldsky_network_assets,
)

metal_network = goldsky_network_assets(
    network_name="metal",
    destination_dataset_name="superchain",
    working_destination_dataset_name="oso_raw_sources",
    transactions_config={"source_name": "metal-receipt_transactions"},
)
