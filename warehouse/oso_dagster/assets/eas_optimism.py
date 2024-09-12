from datetime import datetime, timedelta

import dlt
from dagster import AssetExecutionContext, WeeklyPartitionsDefinition
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from oso_dagster.factories import dlt_factory, pydantic_to_dlt_nullable_columns
from pydantic import BaseModel

from .open_collective import generate_steps


class Attestation(BaseModel):
    id: str
    data: str
    decodedDataJson: str
    recipient: str
    attester: str
    time: int
    timeCreated: int
    expirationTime: int
    revocationTime: int
    refUID: str
    revocable: bool
    revoked: bool
    txid: str
    schemaId: str
    ipfsHash: str
    isOffchain: bool


# The first attestation on EAS Optimism was created on the 07/28/2023 9:22:35 am
EAS_OPTIMISM_FIRST_ATTESTATION = datetime.fromtimestamp(1690557755)

# A sensible limit for the number of nodes to fetch per page
EAS_OPTIMISM_STEP_NODES_PER_PAGE = 10_000


def get_optimism_eas_data(
    context: AssetExecutionContext, client: Client, date_from: float, date_to: float
):
    """
    Retrieves the attestation data from the EAS Optimism GraphQL API.

    Args:
        context (AssetExecutionContext): The asset execution context.
        client (Client): The GraphQL client.
        date_from (float): The start date in timestamp format.
        date_to (float): The end date in timestamp format.

    Yields:
        list: A list of attestation nodes retrieved from EAS Optimism.

    Returns:
        list: An empty list if an exception occurs during the query execution.
    """

    total_query = gql(
        """
        query _count($where: AttestationWhereInput) {
            aggregateAttestation(where: $where) {
                _count {
                    _all
                }
            }
        }        
        """
    )

    total = client.execute(
        total_query,
        variable_values={
            "where": {
                "time": {
                    "gte": date_from,
                    "lte": date_to,
                }
            },
        },
    )

    total_count = total["aggregateAttestation"]["_count"]["_all"]

    context.log.info(f"Total count of attestations: {total_count}")

    attestations_query = gql(
        """
        query Attestations($take: Int, $skip: Int, $where: AttestationWhereInput) {
            attestations(take: $take, skip: $skip, where: $where) {
                id
                data
                decodedDataJson
                recipient
                attester
                time
                timeCreated
                expirationTime
                revocationTime
                refUID
                revocable
                revoked
                txid
                schemaId
                ipfsHash
                isOffchain
            }
        }
        """
    )

    for step in generate_steps(total_count, EAS_OPTIMISM_STEP_NODES_PER_PAGE):
        try:
            query = client.execute(
                attestations_query,
                variable_values={
                    "take": EAS_OPTIMISM_STEP_NODES_PER_PAGE,
                    "skip": step,
                    "where": {
                        "time": {
                            "gte": date_from,
                            "lte": date_to,
                        },
                    },
                },
            )
            context.log.info(
                f"Fetching attestation {step}/{total_count}",
            )
            yield query["attestations"]
        except Exception as exception:
            context.log.warning(
                f"An error occurred while fetching EAS data: '{exception}'. "
                "We will stop this materialization instead of retrying for now."
            )
            return []


def get_optimism_eas(context: AssetExecutionContext, client: Client):
    """
    Get the attestation data from the EAS Optimism GraphQL API.

    Args:
        context (AssetExecutionContext): The asset execution context.
        client (Client): The GraphQL client.

    Yields:
        Generator: A generator that yields the attestation data.
    """

    start = datetime.strptime(context.partition_key, "%Y-%m-%d")
    end = start + timedelta(weeks=1)

    yield from get_optimism_eas_data(
        context, client, start.timestamp(), end.timestamp()
    )


@dlt_factory(
    key_prefix="ethereum_attestation_service_optimism",
    partitions_def=WeeklyPartitionsDefinition(
        start_date=EAS_OPTIMISM_FIRST_ATTESTATION.isoformat().split("T")[0],
        end_date=(datetime.now()).isoformat().split("T")[0],
    ),
)
def attestations(context: AssetExecutionContext):
    """
    Create an asset that retrieves the attestation data from the EAS Optimism GraphQL API.

    Args:
        context (AssetExecutionContext): The asset execution context.

    Yields:
        Asset: The asset that retrieves the attestation data.
    """

    transport = AIOHTTPTransport(url="https://optimism.easscan.org/graphql")
    client = Client(transport=transport, fetch_schema_from_transport=True)

    yield dlt.resource(
        get_optimism_eas(context, client),
        name="attestations",
        columns=pydantic_to_dlt_nullable_columns(Attestation),
        primary_key="id",
    )
