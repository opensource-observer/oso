from typing import Any

from dagster import AssetExecutionContext
from oso_dagster.config import DagsterConfig
from oso_dagster.factories.dlt import dlt_factory
from oso_dagster.factories.graphql import (
    GraphQLResourceConfig,
    PaginationConfig,
    PaginationType,
    graphql_factory,
)


def projects_for_round(
    context: AssetExecutionContext, global_config: DagsterConfig, data: Any
):
    """
    Dependency function that creates a GraphQL resource for each QF round.
    Uses the round ID from upstream data to fetch projects for that specific round.
    """
    round_id = data["id"]

    config = GraphQLResourceConfig(
        name=f"giveth_projects_round_{round_id}",
        endpoint="https://mainnet.serve.giveth.io/graphql",
        target_type="Query",
        target_query="allProjects",
        parameters={
            "qfRoundId": {
                "type": "Int!",
                "value": int(round_id),
            },
        },
        exclude=[
            "projects.addresses.project",
            "projects.projectPower.projectId",
            "projects.projectPower.project",
        ],
        transform_fn=lambda result: result["allProjects"]["projects"],
        pagination=PaginationConfig(
            type=PaginationType.OFFSET,
            page_size=10,
            offset_field="skip",
            limit_field="take",
            rate_limit_seconds=2.0,
        ),
        max_depth=3,
    )

    yield from graphql_factory(config, global_config, context)


@dlt_factory(
    key_prefix="giveth",
)
def qf_rounds(context: AssetExecutionContext, global_config: DagsterConfig):
    """
    Main asset that fetches QF rounds and creates dependent project assets.
    """
    config = GraphQLResourceConfig(
        name="qf_rounds",
        endpoint="https://mainnet.serve.giveth.io/graphql",
        target_type="Query",
        target_query="qfRounds",
        parameters={
            "activeOnly": {
                "type": "Boolean!",
                "value": False,
            },
        },
        transform_fn=lambda result: result["qfRounds"],
        max_depth=2,
        deps=[projects_for_round],
        deps_rate_limit_seconds=1.0,
    )

    yield graphql_factory(
        config, global_config, context, max_table_nesting=0, write_disposition="replace"
    )
