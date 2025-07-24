# TODO(jabolo): Delete this file when done with brainstorming.
"""
def my_dependency(data: Unknown) -> Generator[dlt.resource]:
  safe_parsed = somehow_validate(data)

  all_ids = [x["id"] for x in safe_parsed["data"]]

  for id in all_ids:
    yield from graphql_factory(
      config=Config(
        ...,
        deps=[]
      )
    )

@dlt_factory(...)
def example_asset(config: DagsteConfig) -> Generator[dlt.resource]:

    # This is a Generator[dlt.resource]
    initial_factory = graphql_factory(
      config=Config(
        ...
        deps=[my_dependency]
      )
    )

    yield from initial_factory
"""

from dagster import AssetExecutionContext

from ..factories.dlt import dlt_factory
from ..factories.graphql import (
    GraphQLResourceConfig,
    PaginationConfig,
    PaginationType,
    graphql_factory,
)


@dlt_factory(
    key_prefix="oc_v2",
)
def expenses(
    context: AssetExecutionContext,
):
    config = GraphQLResourceConfig(
        name="expenses",
        endpoint="https://api.opencollective.com/graphql/v2",
        target_type="Query",
        target_query="transactions",
        parameters={
            "type": {"type": "TransactionType!", "value": "DEBIT"},
            "dateFrom": {"type": "DateTime!", "value": "2024-01-23T05:00:00.000Z"},
            "dateTo": {"type": "DateTime!", "value": "2025-01-01T00:00:00.000Z"},
        },
        exclude=["loggedInAccount", "me"],
        transform_fn=lambda result: result["transactions"]["nodes"],
        pagination=PaginationConfig(
            type=PaginationType.OFFSET,
            page_size=100,
            max_pages=5,
            offset_field="offset",
            limit_field="limit",
            total_count_path="totalCount",
            rate_limit_seconds=1.0,
        ),
        max_depth=2,
        deps=[],
    )

    yield graphql_factory(config, context, max_table_nesting=0)
