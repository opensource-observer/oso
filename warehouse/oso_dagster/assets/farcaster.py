from ..factories import (
    create_bq_dts_asset,
    BqDtsAssetConfig,
)
from ..utils.bq_dts import BigQuerySourceConfig
from ..utils.common import TimeInterval, SourceMode

farcaster_data = create_bq_dts_asset(
    BqDtsAssetConfig(
        key_prefix="farcaster",
        asset_name="bq_dts_source",
        display_name="farcaster",
        destination_project_id="opensource-observer",
        destination_dataset_name="farcaster",
        source_config=BigQuerySourceConfig(
            source_project_id="glossy-odyssey-366820",
            source_dataset_name="farcaster",
            service_account=None
        ),
        copy_interval=TimeInterval.Weekly,
        copy_mode=SourceMode.Overwrite,
    ),
)
