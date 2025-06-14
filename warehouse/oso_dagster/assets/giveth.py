import polars as pl

from oso_dagster.config import DagsterConfig
from ..factories.common import AssetFactoryResponse, early_resources_asset_factory
from ..factories.graphql import (
    graphql_factory,
    GraphQLResourceConfig,
    PaginationConfig,
    PaginationType,
)


@early_resources_asset_factory()
def giveth__qf_rounds_v4(global_config: DagsterConfig) -> AssetFactoryResponse:
    """Fetch Giveth QF rounds data using GraphQL factory with pagination"""
    
    # Configuration for QF Rounds with pagination support
    qf_rounds_config = GraphQLResourceConfig(
        name="giveth_qf_rounds_v4",
        endpoint="https://mainnet.serve.giveth.io/graphql",
        target_type="Query",
        target_query="qfRounds",
        max_depth=3,
        pagination=PaginationConfig(
            type=PaginationType.OFFSET,
            page_size=100,  # Larger page size for QF rounds since there are typically fewer of them
            offset_field="skip",
            limit_field="take",
            max_pages=10,  # Reasonable limit for QF rounds
            rate_limit_seconds=0.5,  # Be respectful to the API
        ),
        parameters={
            "activeOnly": {"type": "Boolean!", "value": False},
            "skip": {"type": "Int!", "value": 0},
            "take": {"type": "Int!", "value": 100},
            "orderBy": {
                "type": "OrderByInput", 
                "value": {"field": "CreationDate", "direction": "DESC"}
            }
        },
    )
    
    # Get the GraphQL factory function and call it to get the asset
    graphql_asset_func = graphql_factory(qf_rounds_config)
    
    # Call the function with global_config to get the actual DLT asset
    dlt_asset = graphql_asset_func(global_config)
    
    # Return the DLT asset wrapped in AssetFactoryResponse
    return AssetFactoryResponse(assets=[dlt_asset])


@early_resources_asset_factory()
def giveth__projects_by_round_v4(global_config: DagsterConfig) -> AssetFactoryResponse:
    """Fetch Giveth projects data using GraphQL factory with pagination"""
    
    # Configuration for Projects with pagination (hardcoded round for now)
    projects_config = GraphQLResourceConfig(
        name="giveth_projects_v4",
        endpoint="https://mainnet.serve.giveth.io/graphql",
        target_type="Query",
        target_query="allProjects",
        max_depth=4,
        pagination=PaginationConfig(
            type=PaginationType.OFFSET,
            page_size=50,
            offset_field="skip",
            limit_field="take",
            rate_limit_seconds=0.5,
        ),
        parameters={
            "qfRoundId": {"type": "Int!", "value": 1},  # Hardcoded for now
            "orderBy": {
                "type": "OrderByInput",
                "value": {"field": "CreationDate", "direction": "DESC"},
            },
        },
        # Transform function to extract projects from allProjects response
        transform_fn=lambda result: result.get("allProjects", {}).get("projects", [])
    )
    
    # Get the GraphQL factory function and call it to get the asset
    graphql_asset_func = graphql_factory(projects_config)
    
    # Call the function with global_config to get the actual DLT asset
    dlt_asset = graphql_asset_func(global_config)
    
    # Return the DLT asset wrapped in AssetFactoryResponse
    return AssetFactoryResponse(assets=[dlt_asset])