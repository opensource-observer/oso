from datetime import datetime, timedelta
from typing import Optional

import dlt
from dagster import AssetExecutionContext, WeeklyPartitionsDefinition
from gql import Client, gql
from gql.transport.requests import AIOHTTPTransport
from oso_dagster.factories import dlt_factory, pydantic_to_dlt_nullable_columns
from pydantic import BaseModel


class Attestation(BaseModel):
    attester: str
    data: str
    decodedDataJson: str
    expirationTime: int
    id: str
    ipfsHash: str
    isOffchain: bool
    recipient: str
    refUID: str
    revocable: bool
    revocationTime: int
    revoked: bool
    schemaId: str
    time: int
    txid: str
    

# The first attestation on EAS Optimism was created on the 07/28/2023 9:22:35 am
EAS_OPTIMISM_FIRST_ATTESTATION = 1690524000

# The maximum number of nodes that can be retrieved per page
EAS_OPTIMISM_MAX_NODES_PER_PAGE = 1000

def generate_steps(total: int, step: int):

    for i in range(0, total, step):
        yield i
    if total % step != 0:
        yield total


def get_optimism_eas_data(dateFrom: int, dateTo: int):

    transport = AIOHTTPTransport(url="https://optimism.easscan.org/graphql")
    client = Client(transport=transport, fetch_schema_from_transport=True)

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
                    "gte": dateFrom,
                    "lte": dateTo
                }
            }
        },
    )

    total_count = total["aggregateAttestation"]["_count"]["_all"]

    #context.log.info(f"Total count of attestations: {total_count}")

    attestations_query = gql(
        """
        query Attestations($take: Int, $skip: Int, $where: AttestationWhereInput) {
            attestations(take: $take, skip: $skip, where: $where) {
                attester
                data
                decodedDataJson
                expirationTime
                id
                ipfsHash
                isOffchain
                recipient
                refUID
                revocable
                revocationTime
                revoked
                schemaId
                time
                txid
            }
        }
    """
    )

    for step in generate_steps(total_count, EAS_OPTIMISM_MAX_NODES_PER_PAGE):
        try:
            query = client.execute(
                attestations_query,
                variable_values={
                    "take": EAS_OPTIMISM_MAX_NODES_PER_PAGE,
                    "skip": step,
                    "where": {
                        "time": {
                            "gte": dateFrom,
                            "lte": dateTo
                        }
                    }
                },
            )

            
            context.log.info(
                f"Fetching attestation {step}/{total_count}"
            )
            
            
            yield query["attestations"]

        except Exception as exception:

            context.log.warning(
                f"An error occurred while fetching EAS data: '{exception}'. "
                "We will stop this materialization instead of retrying for now."
            )
            return []


def get_optimism_eas(context: AssetExecutionContext):

    start = datetime.strptime(context.partition_key, "%Y-%m-%d")
    end = start + timedelta(weeks=1) 

    start_date = start.timestamp() 
    end_date = end.timestamp()

    yield from get_optimism_eas_data(context, start_date, end_date)

@dlt_factory(
    key_prefix="ethereum_attestation_service_optimism",
    partitions_def=WeeklyPartitionsDefinition(
        start_date=EAS_OPTIMISM_FIRST_ATTESTATION,
        end_date=datetime.now().timestamp(), 
    ),
)
def attestations(context: AssetExecutionContext):
    yield dlt.resource(
        get_optimism_eas(context),
        name="attestations",
        columns=pydantic_to_dlt_nullable_columns(Attestation),
        primary_key="id",
    )
    