from ..factories.goldsky import goldsky_network_assets

cyber_network = goldsky_network_assets(
    network_name="cyber",
    destination_dataset_name="superchain",
    working_destination_dataset_name="oso_raw_sources",
    traces_enabled=False,
)
