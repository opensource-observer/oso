import os

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


def get_endpoint():
    # TODO: the api key should be fetched from secrets utils (?)
    # TODO: The endpoint including API key will be logged in dagster.
    # TODO: if that's public, it could be a security risk.
    # ENDPOINT = "https://api.goldsky.com/api/public/project_cmeb2e0d63tv701xhfnw8axvf/subgraphs/ens/1.0/gn"
    return f"https://gateway.thegraph.com/api/{os.environ['ENS_API_KEY']}/subgraphs/id/5XqPmWe6gjyrJtFn9cLy237i4cWw2j9HcUJEXsP5qGtH"


@dlt_factory(
    key_prefix="ens",
)
def text_changeds(context: AssetExecutionContext, global_config: DagsterConfig):
    config = GraphQLResourceConfig(
        name="text_changeds",
        endpoint=get_endpoint(),
        target_type="Query",
        target_query="textChangeds",
        max_depth=1,
        parameters={"orderBy": {"type": "TextChanged_orderBy", "value": "blockNumber"}},
        # exclude=[
        # Keep all relevant fields for text changes
        # "id",
        # "resolver",
        # "blockNumber",
        # "transactionID",
        # "key",
        # "value",
        # ],
        transform_fn=lambda result: result["textChangeds"],
        pagination=PaginationConfig(
            type=PaginationType.OFFSET,
            page_size=500,
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

    yield graphql_factory(
        config, global_config, context, max_table_nesting=0, write_disposition="replace"
    )


@dlt_factory(
    key_prefix="ens",
)
def domains(context: AssetExecutionContext, global_config: DagsterConfig):
    context.log.info("ENS Fetcher version 1.16")
    config = GraphQLResourceConfig(
        name="domains",
        endpoint=get_endpoint(),
        target_type="Query",
        target_query="domains",
        max_depth=2,
        transform_fn=lambda result: result["domains"],
        parameters={"orderBy": {"type": "Domain_orderBy", "value": "createdAt"}},
        pagination=PaginationConfig(
            type=PaginationType.OFFSET,
            page_size=50,
            offset_field="skip",
            limit_field="first",
            rate_limit_seconds=2.0,
        ),
        # exclude=[
        #     # "id",
        #     # "name",
        #     "labelhash",
        #     "labelName",
        #     "parent",
        #     "subdomains",
        #     "subdomainCount",
        #     "resolvedAddress",
        #     # "resolver",
        #     "ttl",
        #     "isMigrated",
        #     # "createdAt",
        #     # "owner",
        #     "registrant",
        #     "wrappedOwner",
        #     "expiryDate",
        #     "registration",
        #     "wrappedDomain",
        #     "events",
        #     "key",
        # ],
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
