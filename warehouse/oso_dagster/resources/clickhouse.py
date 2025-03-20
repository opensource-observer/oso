from contextlib import contextmanager

import clickhouse_connect
from dagster import ConfigurableResource, ResourceDependency
from metrics_tools.transfer.clickhouse import ClickhouseImporter
from pydantic import Field

from ..utils import SecretReference, SecretResolver
from ..utils.common import ensure

"""
Note: This code is predominantly copied from the BigQueryResource
It simply returns a Clickhouse Connect Client
"""


class ClickhouseResource(ConfigurableResource):
    """Resource for interacting with Clickhouse.

    Examples:
        .. code-block:: python

            @asset
            def tables(clickhouse: ClickhouseResource):
                with clickhouse.get_client() as client:
                    client.query(...)

            defs = Definitions(
                assets=[tables],
                resources={
                    "clickhouse": ClickhouseResource()
                }
            )
    """

    secrets: ResourceDependency[SecretResolver]

    secret_group_name: str

    host: str = Field(
        default="host",
        description="Clickhouse host.",
    )

    user: str = Field(
        default="user",
        description="Clickhouse username.",
    )

    password: str = Field(
        default="password",
        description="Clickhouse password.",
    )

    @contextmanager
    def get_client(self):
        host = self.secrets.resolve_as_str(
            SecretReference(group_name=self.secret_group_name, key=self.host)
        )
        username = self.secrets.resolve_as_str(
            SecretReference(group_name=self.secret_group_name, key=self.user)
        )
        password = self.secrets.resolve_as_str(
            SecretReference(group_name=self.secret_group_name, key=self.password)
        )
        # Context manager to create a Clickhouse Client.
        ensure(host, "Missing DAGSTER__CLICKHOUSE_HOST (if using local secrets)")
        ensure(username, "Missing DAGSTER__CLICKHOUSE__USER (if using local secrets)")
        ensure(
            password, "Missing DAGSTER__CLICKHOUSE__PASSWORD (if using local secrets)"
        )
        client = clickhouse_connect.get_client(
            host=host, username=username, password=password, secure=True
        )
        yield client


class ClickhouseImporterResource(ConfigurableResource):
    clickhouse: ResourceDependency[ClickhouseResource]
    secrets: ResourceDependency[SecretResolver]

    secret_group_name: str

    access_key: str = Field(
        default="host",
        description="Clickhouse host.",
    )

    secret_key: str = Field(
        default="user",
        description="Clickhouse username.",
    )

    @contextmanager
    def get(self):
        access_key = self.secrets.resolve_as_str(
            SecretReference(group_name=self.secret_group_name, key=self.access_key)
        )
        secret_key = self.secrets.resolve_as_str(
            SecretReference(group_name=self.secret_group_name, key=self.secret_key)
        )
        with self.clickhouse.get_client() as client:
            yield ClickhouseImporter(
                client, access_key=access_key, secret_key=secret_key
            )
