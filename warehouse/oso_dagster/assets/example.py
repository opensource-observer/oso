# TODO(jabolo): Delete this file when done with brainstorming.
from typing import Any

from dagster import AssetExecutionContext

from ..factories.dlt import dlt_factory
from ..factories.graphql import (
    GraphQLResourceConfig,
    PaginationConfig,
    PaginationType,
    graphql_factory,
)


def from_account_users(context: AssetExecutionContext, data: Any):
    config = GraphQLResourceConfig(
        name=f"account_query_{data['fromAccount']['id']}",
        endpoint="https://api.opencollective.com/graphql/v2",
        target_type="Query",
        target_query="account",
        exclude=["feed", "stats", "parentAccount"],
        parameters={
            "id": {
                "type": "String",
                "value": data["fromAccount"]["id"],
            },
        },
        transform_fn=lambda result: result["account"],
        max_depth=2,
    )

    yield from graphql_factory(config, context, max_table_nesting=0)


@dlt_factory(
    key_prefix="oc_v2",
)
def account_users(
    context: AssetExecutionContext,
):
    config = GraphQLResourceConfig(
        name="account_users",
        endpoint="https://api.opencollective.com/graphql/v2",
        target_type="Query",
        target_query="transactions",
        parameters={
            "type": {"type": "TransactionType!", "value": "DEBIT"},
            "dateFrom": {"type": "DateTime!", "value": "2023-01-23T05:00:00.000Z"},
            "dateTo": {"type": "DateTime!", "value": "2024-01-01T00:00:00.000Z"},
        },
        exclude=["loggedInAccount", "me"],
        transform_fn=lambda result: result["transactions"]["nodes"],
        pagination=PaginationConfig(
            type=PaginationType.OFFSET,
            page_size=5,
            max_pages=2,
            offset_field="offset",
            limit_field="limit",
            total_count_path="totalCount",
            rate_limit_seconds=5.0,
        ),
        deps_rate_limit_seconds=5.0,
        max_depth=2,
        deps=[from_account_users],
    )

    yield graphql_factory(config, context, max_table_nesting=0)
