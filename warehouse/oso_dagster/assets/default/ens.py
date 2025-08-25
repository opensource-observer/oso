import os
from typing import Any

from dagster import AssetExecutionContext
from oso_dagster.config import DagsterConfig
from oso_dagster.factories.dlt import dlt_factory
from oso_dagster.factories.graphql import (
    GraphQLResourceConfig,
    PaginationConfig,
    PaginationType,
    RetryConfig,
    graphql_factory,
)


def text_changeds_for_domain(
    context: AssetExecutionContext, global_config: DagsterConfig, data: Any
):
    if not (data and data.get("resolver")):
        return

    resolver_id = data["resolver"]["id"]

    config = GraphQLResourceConfig(
        name=f"ens_text_changeds_for_resolver_{resolver_id}",
        # TODO: the api key should be fetched from secrets utils (?)
        endpoint=f"https://gateway.thegraph.com/api/{os.environ['ENS_API_KEY']}/subgraphs/id/5XqPmWe6gjyrJtFn9cLy237i4cWw2j9HcUJEXsP5qGtH",
        target_type="Query",
        target_query="textChangeds",
        max_depth=1,
        parameters={
            "where": {
                "type": "TextChangeds_filter!",
                "value": {"resolver_": {"id": resolver_id}},
            }
        },
        exclude=[
            # "id",
            "resolver",
            # "blockNumer",
            # "transactionID",
            # "key",
            # "value",
        ],
        transform_fn=lambda result: result["textChangeds"],
        pagination=PaginationConfig(
            type=PaginationType.OFFSET,
            page_size=10,
            max_pages=2,
            offset_field="skip",
            limit_field="first",
            rate_limit_seconds=2.0,
        ),
        retry=RetryConfig(
            max_retries=10,
            initial_delay=1.0,
            max_delay=5.0,
            backoff_multiplier=1.5,
            jitter=True,
            reduce_page_size=True,
            min_page_size=1,
            page_size_reduction_factor=0.6,
        ),
    )

    yield from graphql_factory(config, global_config, context)


@dlt_factory(
    key_prefix="ens",
)
def domains(context: AssetExecutionContext, global_config: DagsterConfig):
    config = GraphQLResourceConfig(
        name="domains",
        # endpoint="https://api.goldsky.com/api/public/project_cmeb2e0d63tv701xhfnw8axvf/subgraphs/ens/1.0/gn",
        # TODO: the api key should be fetched from secrets utils (?)
        # TODO: The endpoint including API key will be logged in dagster.
        # TODO: if that's public, it could be a security risk.
        endpoint=f"https://gateway.thegraph.com/api/{os.environ['ENS_API_KEY']}/subgraphs/id/5XqPmWe6gjyrJtFn9cLy237i4cWw2j9HcUJEXsP5qGtH",
        target_type="Query",
        target_query="domains",
        max_depth=1,
        transform_fn=lambda result: result["domains"],
        pagination=PaginationConfig(
            type=PaginationType.OFFSET,
            page_size=10,
            max_pages=2,  # this should be removed in production
            offset_field="skip",
            limit_field="first",
            rate_limit_seconds=2.0,
        ),
        exclude=[
            "id",
            # "name",
            "labelhash",
            "labelName",
            "parent",
            "subdomains",
            "subdomainCount",
            "resolvedAddress",
            # "resolver",
            "ttl",
            "isMigrated",
            # "createdAt",
            # "owner",
            "registrant",
            "wrappedOwner",
            "expiryDate",
            "registration",
            "wrappedDomain",
            "events",
        ],
        deps=[text_changeds_for_domain],
        retry=RetryConfig(
            max_retries=10,
            initial_delay=1.0,
            max_delay=5.0,
            backoff_multiplier=1.5,
            jitter=True,
            reduce_page_size=True,
            min_page_size=1,
            page_size_reduction_factor=0.6,
        ),
    )

    yield graphql_factory(
        config, global_config, context, max_table_nesting=0, write_disposition="replace"
    )
