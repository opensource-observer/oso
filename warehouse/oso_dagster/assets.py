import os
import re
import arrow
from typing import Any, Mapping, List
from enum import Enum
from pathlib import Path
from google.api_core.exceptions import BadRequest
import pandas as pd
from dataclasses import dataclass
from dagster import AssetExecutionContext, AssetKey, MaterializeResult
from dagster_gcp import BigQueryResource, GCSResource

from dagster_dbt import DbtCliResource, dbt_assets, DagsterDbtTranslator
from dagster import asset
from .constants import main_dbt_manifest_path


class Interval(Enum):
    Hourly = 0
    Daily = 1
    Weekly = 2
    Monthly = 3


class SourceMode(Enum):
    Incremental = 0
    Overwrite = 1


@dataclass
class BaseGCSAsset:
    project_id: str
    bucket_name: str
    path_base: str
    file_match: str
    destination_table: str
    raw_dataset_name: str
    clean_dataset_name: str


@dataclass
class IntervalGCSAsset(BaseGCSAsset):
    interval: Interval
    mode: SourceMode
    retention_days: int


class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    def __init__(self, prefix: str):
        self._prefix = prefix

    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        return super().get_asset_key(dbt_resource_props).with_prefix(self._prefix)


@dbt_assets(
    manifest=main_dbt_manifest_path,
    dagster_dbt_translator=CustomDagsterDbtTranslator("main"),
)
def main_dbt_assets(context: AssetExecutionContext, main_dbt: DbtCliResource):
    yield from main_dbt.cli(["build"], context=context).stream()


# @dbt_assets(
#     manifest=source_dbt_manifest_path,
#     dagster_dbt_translator=CustomDagsterDbtTranslator("sources"),
# )
# def source_dbt_assets(context: AssetExecutionContext, source_dbt: DbtCliResource):
#     yield from source_dbt.cli(["build"], context=context).stream()


@asset(key_prefix="sources")
def iris_data(bigquery: BigQueryResource) -> MaterializeResult:
    iris_df = pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
        names=[
            "sepal_length_cm",
            "sepal_width_cm",
            "petal_length_cm",
            "petal_width_cm",
            "species",
        ],
    )

    with bigquery.get_client() as client:
        client.create_dataset("oso_raw_sources", exists_ok=True)
        job = client.load_table_from_dataframe(
            dataframe=iris_df,
            destination="oso_raw_sources.test__iris_data",
        )
        job.result()
    return MaterializeResult(
        metadata={
            "num_records": 100,
        }
    )


def parse_interval_prefix(interval: Interval, prefix: str) -> arrow.Arrow:
    return arrow.get(prefix, "YYYYMMDD")


def interval_gcs_import_asset(key: str, config: IntervalGCSAsset, **kwargs):
    # Find all of the "intervals" in the bucket and load them into the `raw_sources` dataset
    # Run these sources through a secondary dbt model into `clean_sources`

    @asset(key=key, **kwargs)
    def gcs_asset(
        context: AssetExecutionContext, bigquery: BigQueryResource, gcs: GCSResource
    ) -> MaterializeResult:
        # Check the current state of the bigquery db (we will only load things
        # that are new than that). We continously store the imported data in
        # {project}.{dataset}.{table}_{interval_prefix}.
        with bigquery.get_client() as bq_client:
            latest = arrow.get("1970-01-01")
            try:
                rows = bq_client.query_and_wait(
                    f"""
                SELECT DISTINCT _TABLE_SUFFIX
                FROM `{config.project_id}.{config.raw_dataset_name}.{config.destination_table}__*`
                """
                )
            except BadRequest as exc:
                if "any table" in exc.message:
                    context.log.info("Table doesn't exist")
                else:
                    raise exc

            client = gcs.get_client()
            blobs = client.list_blobs(config.bucket_name, prefix=config.path_base)

            file_matcher = re.compile(config.path_base + "/" + config.file_match)

            matching_blobs = []

            # List all of the files in the prefix
            for blob in blobs:
                match = file_matcher.match(blob.name)
                if not match:
                    print(f"skipping {blob.name}")
                    continue
                try:
                    interval_timestamp = arrow.get(
                        match.group("interval_timestamp"), "YYYY-MM-DD"
                    )
                    matching_blobs.append((interval_timestamp, blob.name))
                except IndexError:
                    print(f"skipping {blob.name}")
                    continue

            sorted_blobs = sorted(
                matching_blobs, key=lambda a: a[0].int_timestamp, reverse=True
            )

            if len(sorted_blobs) == 0:
                return MaterializeResult(
                    metadata={
                        "updated": False,
                        "files_loaded": 0,
                        "latest": latest.format("YYYY-MM-DD"),
                    }
                )

            if sorted_blobs[0][0].int_timestamp > latest.int_timestamp:
                timestamp = sorted_blobs[0][0]
                blob_name = sorted_blobs[0][1]

                interval_table = f"{config.project_id}.{config.raw_dataset_name}.{config.destination_table}__{timestamp.format('YYYYMMDD')}"

                # Run the import of the latest data and overwrite the data
                bq_client.query_and_wait(
                    f"""
                LOAD DATA OVERWRITE `{interval_table}`
                FROM FILES (
                    format = "CSV",
                    uris = ["gs://{config.bucket_name}/{blob_name}"]
                );
                """
                )

                raw_table_ref = bq_client.get_dataset(config.raw_dataset_name).table(
                    f"{config.destination_table}__{timestamp.format('YYYYMMDD')}"
                )
                clean_table_ref = bq_client.get_dataset(
                    config.clean_dataset_name
                ).table(config.destination_table)

                # The clean table is just the overwritten data without any date.
                # We keep old datasets around in case we need to rollback for any reason.
                bq_client.copy_table(
                    raw_table_ref,
                    clean_table_ref,
                    location="US",
                    job_config={
                        "write_disposition": "WRITE_TRUNCATE",
                    },
                )

                return MaterializeResult(
                    metadata={
                        "updated": True,
                        "files_loaded": 1,
                        "latest": timestamp.format("YYYY-MM-DD"),
                    }
                )
            else:
                return MaterializeResult(
                    metadata={
                        "updated": False,
                        "files_loaded": 0,
                        "latest": latest.format("YYYY-MM-DD"),
                    }
                )

    return gcs_asset


karma3_globaltrust = interval_gcs_import_asset(
    "karma3_globaltrust",
    IntervalGCSAsset(
        "opensource-observer",
        "oso-dataset-transfer-bucket",
        "openrank",
        r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/k3l_cast_globaltrust.csv.gz",
        "karma3__globaltrust",
        "oso_raw_sources",
        "oso_sources",
        Interval.Daily,
        SourceMode.Overwrite,
        10,
    ),
)

karma3_globaltrust_config = interval_gcs_import_asset(
    "karma3_globaltrust_config",
    IntervalGCSAsset(
        "opensource-observer",
        "oso-dataset-transfer-bucket",
        "openrank",
        r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/k3l_cast_globaltrust_config.csv.gz",
        "karma3__globaltrust_config",
        "oso_raw_sources",
        "oso_sources",
        Interval.Daily,
        SourceMode.Overwrite,
        10,
    ),
)

karma3_localtrust = interval_gcs_import_asset(
    "karma3_localtrust",
    IntervalGCSAsset(
        "opensource-observer",
        "oso-dataset-transfer-bucket",
        "openrank",
        r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/k3l_cast_localtrust.csv.gz",
        "karma3__localtrust",
        "oso_raw_sources",
        "oso_sources",
        Interval.Daily,
        SourceMode.Overwrite,
        10,
    ),
)
