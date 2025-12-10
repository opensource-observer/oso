import gcsfs
from dagster import ConfigurableResource
from pydantic import Field


class GCSResource(ConfigurableResource):
    """Resource for interacting with GCS."""

    gcs_project: str = Field(description="GCS project name.")

    def get_client(self):
        """Provides a GCS connection."""

        return gcsfs.GCSFileSystem(project=self.gcs_project, asynchronous=True)
