from ..factories import (
    bq_dts_asset,
)
from ..utils.bq_dts import BigQuerySourceConfig
from ..utils.common import TimeInterval, SourceMode

farcaster_data = bq_dts_asset(
    key_prefix="lens",
    asset_name="bq_dts_source",
    display_name="lens",
    destination_project_id="opensource-observer",
    destination_dataset_name="lens_v2_polygon",
    source_config=BigQuerySourceConfig(
        source_project_id="lens-public-data",
        source_dataset_name="v2_polygon",
        service_account=None,
    ),
    copy_interval=TimeInterval.Weekly,
    copy_mode=SourceMode.Overwrite,
)
