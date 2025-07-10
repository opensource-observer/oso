import logging
import dlt
from dagster import AssetKey
from oso_dagster.config import DagsterConfig
from oso_dagster.utils.secrets import SecretResolver
from ..factories.common import AssetFactoryResponse, early_resources_asset_factory
from ..factories.graphql import (
    graphql_factory,
    GraphQLResourceConfig,
    PaginationConfig,
    PaginationType,
)

logger = logging.getLogger(__name__)


@early_resources_asset_factory()
def giveth__qf_rounds_v4(global_config: DagsterConfig, secrets: SecretResolver) -> AssetFactoryResponse:
    """Fetch all QF rounds from Giveth GraphQL API."""
    try:
        logger.info("💫 Starting Giveth QF Rounds asset loading...")
        
        config = GraphQLResourceConfig(
            name="giveth_qf_rounds_v4",
            endpoint="https://mainnet.serve.giveth.io/graphql",
            target_type="Query",
            target_query="qfRounds",
            max_depth=5,
            parameters={
                "activeOnly": {"type": "Boolean!", "value": False},
            },
            pagination=None
        )

        logger.info("Invoking graphql_factory for qfRounds with config: %s", config)

        graphql_func = graphql_factory(config, key_prefix=["giveth"])

        # Get destinations from global config 
        result = graphql_func(
            global_config=global_config,
            secrets=secrets,
            dlt_staging_destination=dlt.destinations.filesystem(
                global_config.staging_bucket_url or "file://./staging"
            ),
            dlt_warehouse_destination=dlt.destinations.duckdb(
                global_config.local_duckdb_path
            ),
            dependencies=[]
        )

        logger.info("✅ Successfully created Giveth QF Rounds asset!")
        return result if isinstance(result, AssetFactoryResponse) else AssetFactoryResponse(assets=[result])

    except Exception as e:
        logger.error("❌ Failed to create Giveth QF Rounds asset: %s", e)
        logger.exception("Full error details:")
        return AssetFactoryResponse(assets=[])


@early_resources_asset_factory()
def giveth__all_projects_v4(global_config: DagsterConfig, secrets: SecretResolver) -> AssetFactoryResponse:
    """Fetch all projects from Giveth GraphQL API."""
    try:
        logger.info("💫 Starting Giveth All Projects asset loading...")
        
        config = GraphQLResourceConfig(
            name="giveth_all_projects_v4",
            endpoint="https://mainnet.serve.giveth.io/graphql",
            target_type="Query",
            target_query="allProjects",
            max_depth=2,
            pagination=PaginationConfig(
                type=PaginationType.OFFSET,
                page_size=100,
                offset_field="skip",
                limit_field="take",
                max_pages=None,
                rate_limit_seconds=0.5,
            ),
            parameters={
                "skip": {"type": "Int", "value": 0},
                "take": {"type": "Int!", "value": 100},
                "orderBy": {
                    "type": "OrderByInput",
                    "value": {"field": "CreationDate", "direction": "DESC"},
                },
            },
        )

        graphql_func = graphql_factory(
            config,
            key_prefix=["giveth", "projects"]
        )

        # Get destinations from global config 
        result = graphql_func(
            global_config=global_config,
            secrets=secrets,
            dlt_staging_destination=dlt.destinations.filesystem(
                global_config.staging_bucket_url or "file://./staging"
            ),
            dlt_warehouse_destination=dlt.destinations.duckdb(
                global_config.local_duckdb_path
            ),
            dependencies=[AssetKey(["giveth", "giveth_qf_rounds_v4"])]
        )

        logger.info("✅ Successfully created Giveth All Projects asset!")
        return result if isinstance(result, AssetFactoryResponse) else AssetFactoryResponse(assets=[result])

    except Exception as e:
        logger.error("❌ Failed to create Giveth All Projects asset: %s", e)
        logger.exception("Full error details:")
        return AssetFactoryResponse(assets=[])