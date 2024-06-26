from ..factories import (
    interval_gcs_import_asset,
    SourceMode,
    Interval,
    IntervalGCSAsset,
)

karma3_globaltrust = interval_gcs_import_asset(
    IntervalGCSAsset(
        key_prefix="karma3",
        name="globaltrust",
        project_id="opensource-observer",
        bucket_name="oso-dataset-transfer-bucket",
        path_base="openrank",
        file_match=r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/k3l_cast_globaltrust.csv.gz",
        destination_table="globaltrust",
        raw_dataset_name="oso_raw_sources",
        clean_dataset_name="karma3",
        interval=Interval.Daily,
        mode=SourceMode.Overwrite,
        retention_days=10,
    ),
)

karma3_globaltrust_config = interval_gcs_import_asset(
    IntervalGCSAsset(
        key_prefix="karma3",
        name="globaltrust_config",
        project_id="opensource-observer",
        bucket_name="oso-dataset-transfer-bucket",
        path_base="openrank",
        file_match=r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/k3l_cast_globaltrust_config.csv.gz",
        destination_table="globaltrust_config",
        raw_dataset_name="oso_raw_sources",
        clean_dataset_name="karma3",
        interval=Interval.Daily,
        mode=SourceMode.Overwrite,
        retention_days=10,
    ),
)

karma3_localtrust = interval_gcs_import_asset(
    IntervalGCSAsset(
        key_prefix="karma3",
        name="localtrust",
        project_id="opensource-observer",
        bucket_name="oso-dataset-transfer-bucket",
        path_base="openrank",
        file_match=r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/k3l_cast_localtrust.csv.gz",
        destination_table="localtrust",
        raw_dataset_name="oso_raw_sources",
        clean_dataset_name="karma3",
        interval=Interval.Daily,
        mode=SourceMode.Overwrite,
        retention_days=10,
    ),
)
