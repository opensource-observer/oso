from contextlib import contextmanager
from typing import Any, Iterator, Optional

from dagster import (
    ConfigurableResource,
    resource,
)
from dagster_gcp.bigquery.utils import setup_gcp_creds
from google.cloud.bigquery_datatransfer import DataTransferServiceClient
from pydantic import Field

"""
Note: This code is predominantly copied from the BigQueryResource
It simply returns a BigQuery DataTransferServiceClient
"""

class BigQueryDataTransferResource(ConfigurableResource):
    """Resource for interacting with Google BigQuery Data Transfer.

    Examples:
        .. code-block:: python

            @asset
            def transfer_configs(bigquery_datatransfer: BigQueryDataTransferResource):
                with bigquery_datatransfer.get_client() as client:
                    client.list_transfer_configs(...)

            defs = Definitions(
                assets=[transfer_configs],
                resources={
                    "bigquery_datatransfer": BigQueryDataTransferResource(project="my-project")
                }
            )
    """

    project: Optional[str] = Field(
        default=None,
        description=(
            "Project ID for the project which the client acts on behalf of. Will be passed when"
            " creating a dataset / job. If not passed, falls back to the default inferred from the"
            " environment."
        ),
    )

    location: Optional[str] = Field(
        default=None,
        description="Default location for jobs / datasets / tables.",
    )

    gcp_credentials: Optional[str] = Field(
        default=None,
        description=(
            "GCP authentication credentials. If provided, a temporary file will be created"
            " with the credentials and ``GOOGLE_APPLICATION_CREDENTIALS`` will be set to the"
            " temporary file. To avoid issues with newlines in the keys, you must base64"
            " encode the key. You can retrieve the base64 encoded key with this shell"
            " command: ``cat $GOOGLE_AUTH_CREDENTIALS | base64``"
        ),
    )

    @contextmanager
    def get_client(self) -> Iterator[DataTransferServiceClient]:
        #Context manager to create a BigQuery Data Transfer Client.
        if self.gcp_credentials:
            with setup_gcp_creds(self.gcp_credentials):
                yield DataTransferServiceClient()

        else:
            yield DataTransferServiceClient()

    def get_object_to_set_on_execution_context(self) -> Any:
        with self.get_client() as client:
            yield client


@resource(
    config_schema=BigQueryDataTransferResource.to_config_schema(),
    description="Dagster resource for connecting to BigQuery Data Transfer",
)
def bigquery_datatransfer_resource(context):
    bq_dts_resource = BigQueryDataTransferResource.from_resource_context(context)
    with bq_dts_resource.get_client() as client:
        yield client
