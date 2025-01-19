from dlt.sources.rest_api.typing import RESTAPIConfig

from ..factories import IntervalGCSAsset, interval_gcs_import_asset
from ..factories.rest import create_rest_factory_asset
from ..utils.common import SourceMode, TimeInterval

config: RESTAPIConfig = {
    "client": {
        "base_url": "https://api.growthepie.xyz/v1",
    },
    "resource_defaults": {
        "write_disposition": "replace",
    },
    "resources": [
        {
            "name": "fundamentals_full",
            "endpoint": {
                "path": "fundamentals_full.json",
                "data_selector": "$",
            },
        }
    ],
}

dlt_assets = create_rest_factory_asset(
    config=config,
)

growthepie_assets = dlt_assets(
    key_prefix="growthepie",
)

growthepie_oli_data = interval_gcs_import_asset(
    IntervalGCSAsset(
        key_prefix="growthepie",
        name="oli",
        project_id="opensource-observer",
        bucket_name="oso-dataset-transfer-bucket",
        path_base="growthepie/oli",
        file_match=r"oli_tag_mapping_(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d).parquet",
        destination_table="oli_tag_mapping",
        raw_dataset_name="oso_raw_sources",
        clean_dataset_name="growthepie",
        interval=TimeInterval.Daily,
        mode=SourceMode.Overwrite,
        retention_days=30,
        format="PARQUET",
    ),
)