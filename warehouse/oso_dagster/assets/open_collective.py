from datetime import datetime, timedelta
from typing import TypedDict

import dlt
from dagster import AssetExecutionContext, WeeklyPartitionsDefinition
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from oso_dagster.factories import dlt_factory, pydantic_to_dlt_nullable_columns
from oso_dagster.utils.secrets import secret_ref_arg
from pydantic import BaseModel


class Host(TypedDict):
    id: str
    type: str
    slug: str
    name: str
    legalName: str
    description: str
    currency: str
    longDescription: str


class Expense(BaseModel):
    id: str
    legacyId: int
    group: str
    type: str
    kind: str
    hostCurrencyFxRate: int
    createdAt: str
    updatedAt: str
    isRefunded: bool
    isRefund: bool
    isDisputed: bool
    isInReview: bool
    isOrderRejected: bool
    merchantId: str
    invoiceTemplate: str
    host: Host


def generate_steps(total, step):
    for i in range(0, total, step):
        yield i
    if total % step != 0:
        yield total


def get_open_collective_data(client: Client, type: str, dateFrom: str, dateTo: str):
    MAX_PER_PAGE = 100

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
        query ($limit: Int!, $offset: Int!, $type: TransactionType, $dateFrom: DateTime!, $dateTo: DateTime!) {
          transactions(
            limit: $limit
            offset: $offset
            type: $type
            dateFrom: $dateFrom
            dateTo: $dateTo
          ) {
            offset
            limit
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

    for step in generate_steps(total_count, MAX_PER_PAGE):
        try:
            query = client.execute(
                expense_query,
                variable_values={
                    "limit": MAX_PER_PAGE,
                    "offset": step,
                    "type": type,
                    "dateFrom": dateFrom,
                    "dateTo": dateTo,
                },
            )
            yield query["expenses"]["nodes"]
        except Exception as _exception:
            # TODO(jabolo): Use sensors to add delay between
            # calls so as to account for rate limiting instead
            # of aborting the whole process
            return []


@dlt.resource(
    name="open_collective",
    columns=pydantic_to_dlt_nullable_columns(Expense),
)
def get_open_collective_expenses(
    context: AssetExecutionContext,
    client: Client,
    kind: str,
):
    start = datetime.strptime(context.partition_key, "%Y-%m-%d")
    end = start + timedelta(weeks=1)

    start_date = f"{start.isoformat().split(".")[0]}Z"
    end_date = f"{end.isoformat().split(".")[0]}Z"

    yield get_open_collective_data(client, kind, start_date, end_date)


def base_open_collective_client(personal_token: str):
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
        start_date=(datetime.now() - timedelta(weeks=5)).isoformat().split("T")[0],
        end_date=(datetime.now()).isoformat().split("T")[0],
    ),
)
def expenses(
    context: AssetExecutionContext,
    personal_token: str = secret_ref_arg(
        group_name="open_collective", key="personal_token"
    ),
):
    client = base_open_collective_client(personal_token)
    yield from get_open_collective_expenses(context, client, "DEBIT")


@dlt_factory(
    key_prefix="open_collective",
    partitions_def=WeeklyPartitionsDefinition(
        start_date=(datetime.now() - timedelta(weeks=5)).isoformat().split("T")[0],
        end_date=(datetime.now()).isoformat().split("T")[0],
    ),
)
def deposits(
    context: AssetExecutionContext,
    personal_token: str = secret_ref_arg(
        group_name="open_collective", key="personal_token"
    ),
):
    client = base_open_collective_client(personal_token)
    yield from get_open_collective_expenses(context, client, "CREDIT")
