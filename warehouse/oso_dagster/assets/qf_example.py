"""
Example showing how the GraphQL factory already supports asset dependencies
for the Giveth QF rounds use case described in issue #4518.

This demonstrates that the current factory can:
1. Fetch QF rounds as initial data
2. Use round IDs to create dependent assets for projects per round
3. Support dynamic asset creation based on upstream data
"""

from typing import Any

from dagster import AssetExecutionContext

from ..factories.dlt import dlt_factory
from ..factories.graphql import (
    GraphQLResourceConfig,
    PaginationConfig,
    PaginationType,
    graphql_factory,
)

# This is the error we get when we don't exclude the fields.
"""
GraphQL query execution failed: {'message': 'Cannot return null for non-nullable field ProjectPowerView.projectId.', 'locations': [{'line': 954, 'column': 9}], 'path': ['allProjects', 'projects', 0, 'projectPower', 'projectId'], 'extensions': {'code': 'INTERNAL_SERVER_ERROR'}}
"""


def projects_for_round(context: AssetExecutionContext, data: Any):
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
            max_pages=5,
            offset_field="skip",
            limit_field="take",
            rate_limit_seconds=2.0,
        ),
        max_depth=3,
    )

    yield from graphql_factory(config, context, max_table_nesting=0)


@dlt_factory(
    key_prefix="giveth",
)
def qf_rounds(context: AssetExecutionContext):
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
        # This is where the magic happens: each QF round will trigger
        # the creation of a dependent asset for its projects
        deps=[projects_for_round],
        deps_rate_limit_seconds=1.0,
    )

    yield from graphql_factory(config, context, max_table_nesting=0)
