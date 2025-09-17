from typing import Optional

from dagster import AssetExecutionContext, RetryPolicy
from oso_dagster.config import DagsterConfig
from oso_dagster.factories.dlt import dlt_factory
from oso_dagster.factories.graphql import (
    GraphQLResourceConfig,
    PaginationConfig,
    PaginationType,
    RetryConfig,
    graphql_factory,
)
from oso_dagster.utils.secrets import secret_ref_arg

# NOTE: Since we are running on spot instances, we need to set a higher retry
# count to account for the fact that spot instances can be terminated at any time.
MAX_RETRY_COUNT = 25

K8S_CONFIG = {
    "merge_behavior": "SHALLOW",
    "pod_spec_config": {
        "node_selector": {
            "pool_type": "spot",
        },
        "tolerations": [
            {
                "key": "pool_type",
                "operator": "Equal",
                "value": "spot",
                "effect": "NoSchedule",
            }
        ],
    },
}


def get_endpoint(ens_api_key: Optional[str] = None, masked: bool = False) -> str:
    if masked:
        return "https://gateway.thegraph.com/api/***/subgraphs/id/5XqPmWe6gjyrJtFn9cLy237i4cWw2j9HcUJEXsP5qGtH"

    return f"https://gateway.thegraph.com/api/{ens_api_key}/subgraphs/id/5XqPmWe6gjyrJtFn9cLy237i4cWw2j9HcUJEXsP5qGtH"


@dlt_factory(
    key_prefix="ens",
    op_tags={
        "dagster-k8s/config": K8S_CONFIG,
    },
    retry_policy=RetryPolicy(max_retries=MAX_RETRY_COUNT),
)
def text_changeds(
    context: AssetExecutionContext,
    global_config: DagsterConfig,
    ens_api_key: str = secret_ref_arg(group_name="ens", key="api_key"),
):
    config = GraphQLResourceConfig(
        name="text_changeds",
        endpoint=get_endpoint(ens_api_key=ens_api_key),
        masked_endpoint=get_endpoint(masked=True),
        target_type="Query",
        target_query="textChangeds",
        max_depth=1,
        exclude=[
            # "id",
            "resolver",
            # "blockNumber",
            # "transactionID",
            # "key",
            # "value",
        ],
        transform_fn=lambda result: result["textChangeds"],
        pagination=PaginationConfig(
            type=PaginationType.KEYSET,
            page_size=500,
            rate_limit_seconds=2.0,
            order_by_field="id",
            last_value_field="id_gt",
            cursor_key="id",
            page_size_field="first",
            order_direction="asc",
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
        enable_chunked_resume=True,
        checkpoint_field="blockNumber",
    )

    yield graphql_factory(
        config, global_config, context, max_table_nesting=0, write_disposition="replace"
    )


@dlt_factory(
    key_prefix="ens",
    op_tags={
        "dagster-k8s/config": K8S_CONFIG,
    },
    retry_policy=RetryPolicy(max_retries=MAX_RETRY_COUNT),
)
def domains(
    context: AssetExecutionContext,
    global_config: DagsterConfig,
    ens_api_key: str = secret_ref_arg(group_name="ens", key="api_key"),
):
    config = GraphQLResourceConfig(
        name="domains",
        endpoint=get_endpoint(ens_api_key=ens_api_key),
        masked_endpoint=get_endpoint(masked=True),
        target_type="Query",
        target_query="domains",
        max_depth=2,
        transform_fn=lambda result: result["domains"],
        pagination=PaginationConfig(
            type=PaginationType.KEYSET,
            page_size=500,
            rate_limit_seconds=2.0,
            order_by_field="id",
            last_value_field="id_gt",
            cursor_key="id",
            page_size_field="first",
            order_direction="asc",
        ),
        exclude=[
            # "id",
            # "name",
            "labelhash",
            "labelName",
            "parent",
            # "subdomains",
            # "subdomainCount",
            "resolvedAddress",
            # "resolver",
            "ttl",
            "isMigrated",
            "createdAt",
            # "owner",
            # "registrant",
            "wrappedOwner",
            # "expiryDate",
            # "registration",
            "wrappedDomain",
            "events",
        ],
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
        enable_chunked_resume=True,
        checkpoint_field="id",
    )

    yield graphql_factory(
        config, global_config, context, max_table_nesting=0, write_disposition="replace"
    )
