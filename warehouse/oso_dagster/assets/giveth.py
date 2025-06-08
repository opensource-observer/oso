import requests
import polars as pl
from dagster import multi_asset, AssetOut, Output
from typing import Any
from  ..factories.graphql import GraphQLResourceConfig, PaginationConfig, PaginationType

@multi_asset(
    outs={
        "giveth__qf_rounds_v2": AssetOut(),
        "giveth__projects_by_round_v2": AssetOut(),
    },
)
def fetch_giveth_data():
    endpoint = "https://mainnet.serve.giveth.io/graphql"

    # QF Rounds Query Config
    qf_rounds_config = GraphQLResourceConfig(
        name="giveth_qf_rounds",
        endpoint=endpoint,
        target_type="Query",
        target_query="qfRounds(activeOnly: $activeOnly)",
        parameters={
            "activeOnly": {"type": "Boolean!", "value": False}
        }
    )

    # Projects Query Config with pagination
    projects_pagination = PaginationConfig(
        type=PaginationType.OFFSET,
        page_size=50,
        offset_field="skip",
        limit_field="take",
        total_count_path="allProjects.totalCount"  # Assuming this exists in the schema
    )

    projects_config = GraphQLResourceConfig(
        name="giveth_projects",
        endpoint=endpoint,
        target_type="Query",
        target_query="allProjects(qfRoundId: $qfRoundId, skip: $skip, take: $take, orderBy: $orderBy)",
        pagination=projects_pagination,
        parameters={
            "qfRoundId": {"type": "Int!", "value": None},  # Will be set per round
            "skip": {"type": "Int!", "value": 0},
            "take": {"type": "Int!", "value": 50},
            "orderBy": {
                "type": "OrderByInput",
                "value": {
                    "field": "CreationDate",
                    "direction": "DESC"
                }
            }
        }
    )

    @graphql_factory
    def get_qf_rounds(config: GraphQLResourceConfig):
        """Factory for QF Rounds query"""
        pass

    @graphql_factory
    def get_projects(config: GraphQLResourceConfig):
        """Factory for Projects query"""
        pass

    # Execute QF Rounds query
    qf_rounds_resource = get_qf_rounds(qf_rounds_config)
    qf_rounds_data = list(qf_rounds_resource())
    qf_rounds_df = pl.DataFrame(qf_rounds_data)

    print("QF Rounds DF schema:")
    print(qf_rounds_df.schema)
    print("QF Rounds DF preview:")
    print(qf_rounds_df.head(3))

    yield Output(qf_rounds_df, output_name="giveth__qf_rounds_v2")

    # Execute Projects query for each round
    all_projects = []
    for round_data in qf_rounds_data:
        round_id = round_data["id"]
        projects_config.parameters["qfRoundId"]["value"] = round_id
        
        projects_resource = get_projects(projects_config)
        projects_data = list(projects_resource())
        all_projects.extend(projects_data)

    projects_df = pl.DataFrame(all_projects)
    
    print("Projects DF schema:")
    print(projects_df.schema)
    print("Projects DF preview:")
    print(projects_df.head(3))
    yield Output(projects_df, output_name="giveth__projects_by_round_v2")