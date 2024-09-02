from ..factories import (
    bq_dts_asset,
)
from ..utils.bq import BigQueryDatasetConfig
from ..utils.bq_dts import BqDtsSourceConfig
from ..utils.common import TimeInterval, SourceMode

filecoin_data = bq_dts_asset(
    key_prefix="filecoin",
    asset_name="bq_dts_source",
    display_name="filecoin",
    destination_config=BigQueryDatasetConfig(
        project_id="opensource-observer",
        dataset_name="filecoin_lily",
        service_account=None,
    ),
    source_config=BqDtsSourceConfig(
        project_id="lily-data",
        dataset_name="lily",
        service_account=None,
    ),
    copy_interval=TimeInterval.Weekly,
    copy_mode=SourceMode.Overwrite,
)
