from ..factories import (
    bq_dts_asset,
)
from ..utils.bq import BigQueryDatasetConfig
from ..utils.bq_dts import BqDtsSourceConfig
from ..utils.common import TimeInterval, SourceMode

farcaster_data = bq_dts_asset(
    key_prefix="farcaster",
    asset_name="bq_dts_source",
    display_name="farcaster",
    destination_config=BigQueryDatasetConfig(
        project_id="opensource-observer",
        dataset_name="farcaster",
        service_account=None,
    ),
    source_config=BqDtsSourceConfig(
        project_id="glossy-odyssey-366820",
        dataset_name="farcaster",
        service_account=None,
    ),
    copy_interval=TimeInterval.Weekly,
    copy_mode=SourceMode.Overwrite,
)
