from datetime import datetime, timedelta
from typing import Optional

import dlt
from dagster import AssetExecutionContext, WeeklyPartitionsDefinition
from dlt.destinations.adapters import bigquery_adapter
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from oso_dagster import constants
from oso_dagster.factories import dlt_factory, pydantic_to_dlt_nullable_columns
from oso_dagster.utils.secrets import secret_ref_arg
from pydantic import UUID4, BaseModel


class Host(BaseModel):
    id: UUID4
    type: str
    slug: str
    name: Optional[str] = None
    legalName: Optional[str] = None
    description: Optional[str] = None
    currency: Optional[str] = None


class Transaction(BaseModel):
    id: UUID4
    legacyId: int
    group: UUID4
    type: str
    kind: Optional[str] = None
    hostCurrencyFxRate: Optional[float] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    isRefunded: Optional[bool] = None
    isRefund: Optional[bool] = None
    isDisputed: Optional[bool] = None
    isInReview: Optional[bool] = None
    isOrderRejected: bool
    merchantId: Optional[UUID4] = None
    invoiceTemplate: Optional[str] = None
    host: Optional[Host] = None


# The first transaction on Open Collective was on January 23, 2015
OPEN_COLLECTIVE_TX_EPOCH = "2015-01-23T05:00:00.000Z"

# The maximum number of nodes that can be retrieved per page
OPEN_COLLECTIVE_MAX_NODES_PER_PAGE = 1000


def generate_steps(total: int, step: int):
    """
    Generates a sequence of numbers from 0 up to the specified total, incrementing by the specified step.
    If the total is not divisible by the step, the last iteration will yield the remaining value.

    Args:
        total (int): The desired total value.
        step (int): The increment value for each iteration.

    Yields:
        int: The next number in the sequence.

    Example:
        >>> for num in generate_steps(10, 3):
        ...     print(num)
        0
        3
        6
        9
        10
    """

    for i in range(0, total, step):
        yield i
    if total % step != 0:
        yield total


def get_open_collective_data(
    context: AssetExecutionContext,
    client: Client,
    type: str,
    dateFrom: str,
    dateTo: str,
):
    """
    Retrieves Open Collective data using the provided client and query parameters.

    Args:
        context (AssetExecutionContext): The execution context of the asset.
        client (Client): The client object used to execute the GraphQL queries.
        type (str): The transaction type. Either "DEBIT" or "CREDIT".
        dateFrom (str): The start date for the query.
        dateTo (str): The end date for the query.

    Yields:
        list: A list of transaction nodes retrieved from Open Collective.

    Returns:
        list: An empty list if an exception occurs during the query execution.
    """

    total_query = gql(
        """
        query ($type: TransactionType, $dateFrom: DateTime!, $dateTo: DateTime!) {
          transactions(
            type: $type
            dateFrom: $dateFrom
            dateTo: $dateTo
          ) {
            totalCount
          }
        }
        """
    )

    total = client.execute(
        total_query,
        variable_values={
            "type": type,
            "dateFrom": dateFrom,
            "dateTo": dateTo,
        },
    )

    expense_query = gql(
        """
        query ($limit: Int!, $offset: Int!, $type: TransactionType!, $dateFrom: DateTime!, $dateTo: DateTime!) {
          transactions(
            limit: $limit
            offset: $offset
            type: $type
            dateFrom: $dateFrom
            dateTo: $dateTo
          ) {
            totalCount
            nodes {
              id
              legacyId
              group
              type
              kind
              hostCurrencyFxRate
              createdAt
              updatedAt
              isRefunded
              isRefund
              isDisputed
              isInReview
              isOrderRejected
              merchantId
              invoiceTemplate
              host {
                id
                type
                slug
                name
                legalName
                description
                currency
              }
            }
          }
        }
        """
    )

    total_count = total["transactions"]["totalCount"]

    context.log.info(f"Total count of transactions: {total_count}")

    for step in generate_steps(total_count, OPEN_COLLECTIVE_MAX_NODES_PER_PAGE):
        try:
            query = client.execute(
                expense_query,
                variable_values={
                    "limit": OPEN_COLLECTIVE_MAX_NODES_PER_PAGE,
                    "offset": step,
                    "type": type,
                    "dateFrom": dateFrom,
                    "dateTo": dateTo,
                },
            )
            context.log.info(
                f"Fetching transaction {step}/{total_count} for type '{type}'"
            )
            yield query["transactions"]["nodes"]
        except Exception as exception:
            # TODO(jabolo): Implement a retry mechanism
            context.log.warning(
                f"An error occurred while fetching Open Collective data: '{exception}'. "
                "We will stop this materialization instead of retrying for now."
            )
            return []


def get_open_collective_expenses(
    context: AssetExecutionContext,
    client: Client,
    kind: str,
):
    """
    Get open collective expenses.

    Args:
        context (AssetExecutionContext): The asset execution context.
        client (Client): The client object.
        kind (str): The kind of expenses. Either "DEBIT" or "CREDIT".

    Yields:
        Generator: A generator that yields open collective data.
    """

    start = datetime.strptime(context.partition_key, "%Y-%m-%d")
    end = start + timedelta(weeks=1)

    start_date = f"{start.isoformat().split(".")[0]}Z"
    end_date = f"{end.isoformat().split(".")[0]}Z"

    yield from get_open_collective_data(context, client, kind, start_date, end_date)


def base_open_collective_client(personal_token: str):
    """
    Creates and returns a client for interacting with the Open Collective API.

    Args:
        personal_token (str): The personal token used for authentication.

    Returns:
        Client: The Open Collective client.
    """

    transport = RequestsHTTPTransport(
        url="https://api.opencollective.com/graphql/v2",
        use_json=True,
        headers={
            "Personal-Token": personal_token,
        },
    )

    client = Client(
        transport=transport,
        fetch_schema_from_transport=True,
    )

    return client


@dlt_factory(
    key_prefix="open_collective",
    partitions_def=WeeklyPartitionsDefinition(
        start_date=OPEN_COLLECTIVE_TX_EPOCH.split("T")[0],
        end_date=(datetime.now()).isoformat().split("T")[0],
    ),
)
def expenses(
    context: AssetExecutionContext,
    personal_token: str = secret_ref_arg(
        group_name="open_collective", key="personal_token"
    ),
):
    """
    Create and register a Dagster asset that materializes Open Collective expenses.

    Args:
        context (AssetExecutionContext): The execution context of the asset.
        personal_token (str): The personal token for authentication.

    Yields:
        Generator: A generator that yields Open Collective expenses.
    """

    client = base_open_collective_client(personal_token)
    resource = dlt.resource(
        get_open_collective_expenses(context, client, "DEBIT"),
        name="expenses",
        columns=pydantic_to_dlt_nullable_columns(Transaction),
        primary_key="id",
    )

    if constants.enable_bigquery:
        bigquery_adapter(
            resource,
            partition="created_at",
        )

    yield resource


@dlt_factory(
    key_prefix="open_collective",
    partitions_def=WeeklyPartitionsDefinition(
        start_date=OPEN_COLLECTIVE_TX_EPOCH.split("T")[0],
        end_date=(datetime.now()).isoformat().split("T")[0],
    ),
    op_tags={
        "dagster-k8s/config": {
            "container_config": {
                "resources": {
                    "requests": {"cpu": "2000m", "memory": "3584Mi"},
                    "limits": {"cpu": "2000m", "memory": "3584Mi"},
                },
            },
            "pod_spec_config": {
                "node_selector": {"pool_type": "spot",},
                "tolerations": [
                    {
                        "key": "pool_type",
                        "operator": "Equal",
                        "value": "spot",
                        "effect": "PreferNoSchedule",
                    }
                ],
            },
        }
    }
)
def deposits(
    context: AssetExecutionContext,
    personal_token: str = secret_ref_arg(
        group_name="open_collective", key="personal_token"
    ),
):
    """
    Create and register a Dagster asset that materializes Open Collective deposits.

    Args:
        context (AssetExecutionContext): The execution context of the asset.
        personal_token (str): The personal token for authentication.

    Yields:
        Generator: A generator that yields Open Collective deposits.
    """

    client = base_open_collective_client(personal_token)
    resource = dlt.resource(
        get_open_collective_expenses(context, client, "CREDIT"),
        name="funds",
        columns=pydantic_to_dlt_nullable_columns(Transaction),
        primary_key="id",
    )

    if constants.enable_bigquery:
        bigquery_adapter(
            resource,
            partition="created_at",
        )

    yield resource
