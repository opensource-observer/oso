from ..factories.goldsky import goldsky_network_assets


zora_network = goldsky_network_assets(
    network_name="zora",
    destination_dataset_name="superchain",
    working_destination_dataset_name="oso_raw_sources",
)
