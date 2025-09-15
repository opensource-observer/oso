import pynessie
from dagster import ConfigurableResource
from pydantic import Field


class NessieResource(ConfigurableResource):
    """Resource for interacting with Nessie V1 API."""

    url: str = Field(description="Nessie V1 API URL.")

    def get_client(self):
        """Provides a Nessie V1 API connection."""
        return pynessie.init(config_dict={"endpoint": self.url})
