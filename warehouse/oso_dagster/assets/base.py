from ..factories.goldsky import goldsky_network_assets
from ..factories.goldsky.config import NetworkAssetSourceConfigDict

base_network = goldsky_network_assets(
    network_name="base",
    destination_dataset_name="superchain",
    working_destination_dataset_name="oso_raw_sources",
    traces_config=NetworkAssetSourceConfigDict(
        schema_overrides=[
            {"name": "value", "field_type": "STRING"},
        ]
    ),
)
