from ..factories import (
    interval_gcs_import_asset,
    IntervalGCSAsset,
)
from ..factories.sql import sql_assets
from ..utils.common import TimeInterval, SourceMode
from ..utils.secrets import SecretReference

gitcoin_passport_scores = interval_gcs_import_asset(
    IntervalGCSAsset(
        key_prefix="gitcoin",
        name="passport_scores",
        project_id="opensource-observer",
        bucket_name="oso-dataset-transfer-bucket",
        path_base="passport",
        file_match=r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/scores.parquet",
        destination_table="passport_scores",
        raw_dataset_name="oso_raw_sources",
        clean_dataset_name="gitcoin",
        interval=TimeInterval.Daily,
        mode=SourceMode.Overwrite,
        retention_days=10,
        format="PARQUET",
    ),
)

regendata_xyz = sql_assets(
    "gitcoin",
    SecretReference(        
        group_name="gitcoin",
        key="regendata_xyz_database",
    ),
    [
        {
            "table": "grants",
        },
    ],
)