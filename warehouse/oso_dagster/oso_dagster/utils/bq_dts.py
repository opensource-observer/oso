from dataclasses import dataclass
from enum import Enum

from dagster import DagsterLogManager
from google.cloud.bigquery_datatransfer import (
    CreateTransferConfigRequest,
    DataTransferServiceClient,
    DeleteTransferConfigRequest,
    EmailPreferences,
    ListDataSourcesRequest,
    ListTransferConfigsRequest,
    TransferConfig,
)
from google.protobuf.struct_pb2 import Struct

from .bq import BigQueryDatasetConfig
from .common import SourceMode, TimeInterval


# An enum for types of source data
# The value is the `data_source_id` used in Google TransferConfig
# https://cloud.google.com/python/docs/reference/bigquerydatatransfer/latest/google.cloud.bigquery_datatransfer_v1.types.TransferConfig
class BqDtsDataSource(Enum):
    BigQuery = "cross_region_copy"


# Configuration for a BigQuery source
@dataclass(kw_only=True)
class BqDtsBigQuerySourceConfig(BigQueryDatasetConfig):
    # Discriminator field
    source_type: BqDtsDataSource = BqDtsDataSource.BigQuery


# Union type for all the types of source configs
BqDtsSourceConfig = BqDtsBigQuerySourceConfig


# Configuration for BigQuery Data Transfer Service
# Use `to_transfer_config` to convert this to the
# type expected by Google APIs
@dataclass(kw_only=True)
class BqDtsTransferConfig:
    # Name to display in BigQuery console
    display_name: str
    # Destination BigQuery dataset
    destination_config: BigQueryDatasetConfig
    # Source config
    # future: support other source types supported by BQ DTS
    source_config: BqDtsSourceConfig
    # How often we should run this job
    copy_interval: TimeInterval
    # Incremental or overwrite
    copy_mode: SourceMode


# Used to convert a `BqDtsTransferConfig` to the type expected by Google APIs
def to_transfer_config_params(config: BqDtsTransferConfig):
    params = Struct()
    if config.source_config.source_type == BqDtsDataSource.BigQuery:
        params.update(
            {
                "source_project_id": config.source_config.project_id,
                "source_dataset_id": config.source_config.dataset_name,
                "overwrite_destination_table": config.copy_mode == SourceMode.Overwrite,
            }
        )
    # Add parameters for other source_type values here
    else:
        raise ValueError(f"Invalid source_type {config.source_config.source_type}")
    # logger.debug(params)
    return params


# Compare an existing TransferConfig to one specified via Dagster asset
# `match_params` controls whether we only match on destination dataset name or on all parameters
def compare_transfer_config(
    existing: TransferConfig,
    to_compare: BqDtsTransferConfig,
    match_params: bool = False,
):
    # If we're not operating on the same dataset, then shortcut out
    if existing.destination_dataset_id != to_compare.destination_config.dataset_name:
        return False

    # If we don't care to match further fields/params, then let's assume this TransferConfig
    # is what we're looking for
    if not match_params:
        return True

    # Check if the source type/id are the same
    if existing.data_source_id != to_compare.source_config.source_type.value:
        return False

    # Check if parameters are the same
    existingParamDict = dict(existing.params.items())
    newParamDict = dict(to_transfer_config_params(to_compare).items())
    if existingParamDict != newParamDict:
        return False

    # Note: We implicitly ignore `schedule` right now
    return True


# Return the TransferConfig that matches in destination dataset name
def list_transfer_config(client: DataTransferServiceClient, project_id: str):
    # Initialize request argument(s)
    request = ListTransferConfigsRequest(
        parent=f"projects/{project_id}",
    )
    # Make the request
    page_result = client.list_transfer_configs(request=request)
    # Handle the response
    list_result = [x for x in page_result]
    return list_result


# Use this to list all possible data sources and the required parameters
# Google may change this list in the future
def list_data_source_ids(
    client: DataTransferServiceClient,
    config: BqDtsTransferConfig,
    logger: DagsterLogManager,
):
    # Initialize request argument(s)
    request = ListDataSourcesRequest(
        parent=f"projects/{config.destination_config.project_id}",
    )
    # Make the request
    page_result = client.list_data_sources(request=request)
    # Handle the response
    for response in page_result:
        logger.debug(response)


# Call this to update or create the BigQuery Data Transfer job
def ensure_bq_dts_transfer(
    client: DataTransferServiceClient,
    config: BqDtsTransferConfig,
    logger: DagsterLogManager,
):
    # list_data_source_ids(client, config, logger)
    all_existing_configs = list_transfer_config(
        client, config.destination_config.project_id
    )
    # logger.debug(all_existing_configs)
    related_existing_configs = list(
        filter(
            lambda x: compare_transfer_config(x, config, False), all_existing_configs
        )
    )
    # logger.debug(related_existing_configs)
    matching_existing_configs = list(
        filter(lambda x: compare_transfer_config(x, config, True), all_existing_configs)
    )
    # logger.debug(matching_existing_configs)
    if len(matching_existing_configs) > 0:
        logger.info("Found an identical transfer job, skipping...")
        return

    logger.info("Deleting all transfer configs with the same destination dataset")
    for c in related_existing_configs:
        logger.debug(f"Deleting {c.name}")
        client.delete_transfer_config(request=DeleteTransferConfigRequest(name=c.name))

    # We cannot use UpdateTransferConfigRequest because
    # it does not allow changing certain fields (like `source_dataset_id`)
    # So we destroy anything related to that destination dataset
    # and create instead.
    logger.info("Creating new transfer config")
    request = CreateTransferConfigRequest(
        parent=f"projects/{config.destination_config.project_id}",
        transfer_config=TransferConfig(
            destination_dataset_id=config.destination_config.dataset_name,
            display_name=config.display_name,
            data_source_id=config.source_config.source_type.value,
            params=to_transfer_config_params(config),
            schedule="1 of month 00:00"
            if config.copy_interval == TimeInterval.Monthly
            else "every sunday 00:00"
            if config.copy_interval == TimeInterval.Weekly
            else "every 24 hours",
            email_preferences=EmailPreferences(enable_failure_email=True),
        ),
    )
    new_transfer_config = client.create_transfer_config(request=request)
    logger.debug(new_transfer_config)

    # Immediate trigger a run
    # client.start_manual_transfer_runs(request=StartManualTransferRunsRequest(
    #    parent=new_transfer_config.name
    # ))
