from oso_dagster.factories import bq_dts_asset
from oso_dagster.utils.bq import BigQueryDatasetConfig
from oso_dagster.utils.bq_dts import BqDtsSourceConfig
from oso_dagster.utils.common import SourceMode, TimeInterval

lens_data = bq_dts_asset(
    key_prefix="lens",
    asset_name="bq_dts_source",
    display_name="lens",
    destination_config=BigQueryDatasetConfig(
        project_id="opensource-observer",
        dataset_name="lens_v2_polygon",
        service_account=None,
    ),
    source_config=BqDtsSourceConfig(
        project_id="lens-public-data",
        dataset_name="v2_polygon",
        service_account=None,
    ),
    copy_interval=TimeInterval.Weekly,
    copy_mode=SourceMode.Overwrite,
)
