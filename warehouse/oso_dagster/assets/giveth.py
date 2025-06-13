import polars as pl
from dagster import asset, AssetExecutionContext
from typing import Any, Dict, List
from dataclasses import replace

from ..factories.graphql import (
    graphql_factory,
    GraphQLResourceConfig,
    PaginationConfig,
    PaginationType,
)


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """Flatten nested dictionaries"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def align_columns(data: List[Dict]) -> pl.DataFrame:
    """Align columns across all rows and create DataFrame"""
    if not data:
        return pl.DataFrame()
    
    # Get all unique keys across all rows
    all_keys = sorted(set().union(*(row.keys() for row in data)))
    # Ensure every row has all keys (fill with None)
    aligned_data = [
        {key: row.get(key, None) for key in all_keys}
        for row in data
    ]
    return pl.DataFrame(aligned_data, schema=all_keys)


@asset
def giveth__qf_rounds_v3(context: AssetExecutionContext) -> pl.DataFrame:
    """Fetch Giveth QF rounds data using GraphQL factory"""
    endpoint = "https://mainnet.serve.giveth.io/graphql"
    
    context.log.info("Fetching QF Rounds data...")
    
    # Configuration for QF Rounds (no pagination needed)
    qf_rounds_config = GraphQLResourceConfig(
        name="giveth_qf_rounds",
        endpoint=endpoint,
        target_type="Query",
        target_query="qfRounds",
        parameters={"activeOnly": {"type": "Boolean!", "value": False}},
        max_depth=3,  # Adjust based on your schema depth needs
    )
    
    # Create and execute the GraphQL asset
    qf_rounds_asset_func = graphql_factory(qf_rounds_config)
    qf_rounds_resource_generator = qf_rounds_asset_func(context)
    
    # Extract QF rounds data
    qf_rounds_data = []
    for resource in qf_rounds_resource_generator:
        for item in resource:
            flattened_item = flatten_dict(item)
            qf_rounds_data.append(flattened_item)
    
    qf_rounds_df = align_columns(qf_rounds_data)
    
    context.log.info(f"QF Rounds DF schema: {list(qf_rounds_df.columns)}")
    context.log.info(f"Fetched {len(qf_rounds_df)} QF rounds")
    if len(qf_rounds_df) > 0:
        context.log.info(f"QF Rounds sample: {qf_rounds_df.head(3)}")
    
    return qf_rounds_df


@asset(deps=["giveth__qf_rounds_v3"])
def giveth__projects_by_round_v3(
    context: AssetExecutionContext, 
    giveth__qf_rounds_v3: pl.DataFrame
) -> pl.DataFrame:
    """Fetch Giveth projects data for each QF round using GraphQL factory with pagination"""
    endpoint = "https://mainnet.serve.giveth.io/graphql"
    
    context.log.info("Fetching Projects data...")
    
    # Base configuration for Projects with pagination
    base_projects_config = GraphQLResourceConfig(
        name="giveth_projects",
        endpoint=endpoint,
        target_type="Query",
        target_query="allProjects",
        max_depth=4,  # Projects have more nested data
        pagination=PaginationConfig(
            type=PaginationType.OFFSET,
            page_size=50,
            offset_field="skip",
            limit_field="take",
            max_pages=None,  # No limit on pages
            rate_limit_seconds=0.5,  # Be nice to the API
        ),
        parameters={
            "qfRoundId": {"type": "Int!", "value": 0},
            "skip": {"type": "Int!", "value": 0},
            "take": {"type": "Int!", "value": 50},
            "orderBy": {
                "type": "OrderByInput",
                "value": {"field": "CreationDate", "direction": "DESC"},
            },
        },
        # Transform function to extract projects from the allProjects response
        transform_fn=lambda result: result.get("allProjects", {}).get("projects", [])
    )
    
    # Fetch projects for each QF round
    all_projects = []
    qf_rounds_list = giveth__qf_rounds_v3.to_dicts()
    
    context.log.info(f"Processing {len(qf_rounds_list)} QF rounds")
    
    for round_data in qf_rounds_list:
        round_id = round_data.get("id")
        if round_id is None:
            context.log.warning(f"Skipping round with missing ID: {round_data}")
            continue
            
        context.log.info(f"Fetching projects for QF Round ID: {round_id}")
        
        # Create a new config for this specific round
        round_projects_config = replace(
            base_projects_config,
            name=f"giveth_projects_round_{round_id}",
            parameters={
                **base_projects_config.parameters,
                "qfRoundId": {"type": "Int!", "value": int(round_id)}
            }
        )
        
        # Create and execute the GraphQL asset for this round
        projects_asset_func = graphql_factory(round_projects_config)
        projects_resource_generator = projects_asset_func(context)
        
        # Extract projects data for this round
        round_projects_count = 0
        for resource in projects_resource_generator:
            for item in resource:
                flattened_item = flatten_dict(item)
                # Add the round ID for context
                flattened_item["source_qf_round_id"] = round_id
                all_projects.append(flattened_item)
                round_projects_count += 1
        
        context.log.info(f"Fetched {round_projects_count} projects for round {round_id}")
    
    projects_df = align_columns(all_projects)
    
    context.log.info(f"Projects DF schema: {list(projects_df.columns)}")
    context.log.info(f"Total projects fetched: {len(projects_df)}")
    if len(projects_df) > 0:
        context.log.info(f"Projects sample: {projects_df.head(3)}")
    
    return projects_df