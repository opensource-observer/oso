from ..factories import IntervalGCSAsset, interval_gcs_import_asset
from ..utils.common import SourceMode, TimeInterval

openlabelsinitiative_data = interval_gcs_import_asset(
    IntervalGCSAsset(
        key_prefix="openlabelsinitiative",
        name="oli",
        project_id="opensource-observer",
        bucket_name="oso-dataset-transfer-bucket",
        path_base="openlabelsinitiative/oli",
        file_match=r"oli_tag_mapping_(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d).parquet",
        destination_table="oli_tag_mapping",
        raw_dataset_name="oso_raw_sources",
        clean_dataset_name="openlabelsinitiative",
        interval=TimeInterval.Daily,
        mode=SourceMode.Overwrite,
        retention_days=30,
        format="PARQUET",
    ),
)