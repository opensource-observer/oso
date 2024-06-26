from ..factories import (
    interval_gcs_import_asset,
    SourceMode,
    Interval,
    IntervalGCSAsset,
)

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
        interval=Interval.Daily,
        mode=SourceMode.Overwrite,
        retention_days=10,
        format="PARQUET",
    ),
)
