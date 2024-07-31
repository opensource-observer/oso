from ..factories.goldsky import goldsky_network_assets

optimism_network = goldsky_network_assets(
    network_name="optimism",
    destination_dataset_name="superchain",
    working_destination_dataset_name="oso_raw_sources",
)
