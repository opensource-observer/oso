from dataclasses import dataclass, field
from typing import Optional, Sequence, cast

from dagster import AssetExecutionContext, MaterializeResult, ResourceParam, asset
from dagster_gcp import BigQueryResource
from oso_dagster.config import DagsterConfig

from ..resources import BigQueryDataTransferResource
from ..utils import (
    BqDtsTransferConfig,
    DatasetOptions,
    ensure_bq_dts_transfer,
    ensure_dataset,
    unpack_config,
)
from .common import AssetFactoryResponse, GenericAsset


@dataclass(kw_only=True)
class BqDtsAssetConfig(BqDtsTransferConfig):
    # Dagster key prefix
    key_prefix: Optional[str | Sequence[str]] = ""
    # Dagster asset name
    asset_name: str
    # Dagster remaining args
    asset_kwargs: dict = field(default_factory=lambda: {})
    environment: str = "production"


@unpack_config(BqDtsAssetConfig)
def bq_dts_asset(asset_config: BqDtsAssetConfig):
    """
    This is a factory for creating a Dagster asset
    that configures a BigQuery Data Transfer Service job
    """

    tags = {
        "opensource.observer/factory": "bigquery_dts",
        "opensource.observer/environment": asset_config.environment,
        "opensource.observer/type": "source",
        "opensource.observer/source": "stable",
    }

    @asset(
        name=asset_config.asset_name,
        key_prefix=asset_config.key_prefix,
        compute_kind="bigquery_dts",
        tags=tags,
        **asset_config.asset_kwargs,
    )
    def _bq_dts_asset(
        context: AssetExecutionContext,
        global_config: ResourceParam[DagsterConfig],
        bigquery: BigQueryResource,
        bigquery_datatransfer: BigQueryDataTransferResource,
    ) -> MaterializeResult:

        context.log.info(
            f"Materializing a BigQuery Data Transfer asset called {asset_config.asset_name}"
        )
        with bigquery.get_client() as bq_client:
            ensure_dataset(
                bq_client,
                DatasetOptions(
                    dataset_ref=bq_client.dataset(
                        dataset_id=asset_config.destination_config.dataset_name
                    ),
                    is_public=True,
                ),
            )
            context.log.info(
                f"Ensured dataset named {asset_config.destination_config.dataset_name}"
            )

        with bigquery_datatransfer.get_client(global_config) as bq_dts_client:
            context.log.info(
                f"Ensuring BigQuery Data Transfer asset by impersonating {global_config.gcp_impersonate_service_account}"
            )
            ensure_bq_dts_transfer(bq_dts_client, asset_config, context.log)
            context.log.info(
                f"Ensured transfer config named {asset_config.display_name}"
            )

        return MaterializeResult(
            metadata={
                "success": True,
                "name": asset_config.asset_name,
            }
        )

    # https://github.com/opensource-observer/oso/issues/2403
    return AssetFactoryResponse([cast(GenericAsset, _bq_dts_asset)])
