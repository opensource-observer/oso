from ..factories.goldsky import goldsky_network_assets

base_network = goldsky_network_assets(
    network_name="base",
    destination_dataset_name="superchain",
    working_destination_dataset_name="oso_raw_sources",
)
