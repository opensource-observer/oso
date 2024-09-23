from ..factories.goldsky import goldsky_network_assets
from ..factories.goldsky.config import NetworkAssetSourceConfigDict

arbitrum_network = goldsky_network_assets(
    network_name="arbitrum",
    destination_dataset_name="arbitrum_one",
    working_destination_dataset_name="oso_raw_sources",
    traces_config=NetworkAssetSourceConfigDict(
        schema_overrides=[
            {"name": "value", "field_type": "BYTES"},
        ]
    ),
    transactions_config=NetworkAssetSourceConfigDict(
        schema_overrides=[
            {"name": "value", "field_type": "BYTES"},
            {"name": "gas_price", "field_type": "BYTES"},
        ]
    ),
)
