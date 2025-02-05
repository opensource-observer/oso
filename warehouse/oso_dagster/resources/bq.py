import logging
from contextlib import contextmanager

from dagster import ConfigurableResource, ResourceDependency
from dagster_gcp import BigQueryResource
from metrics_tools.transfer.bq import BigQueryImporter

logger = logging.getLogger(__name__)


class BigQueryImporterResource(ConfigurableResource):
    """Resource for providing a BigQueryImporter instance."""

    bigquery: ResourceDependency[BigQueryResource]

    @contextmanager
    def get(self):
        """Provides the BigQueryImporter instance."""
        with self.bigquery.get_client() as client:
            importer = BigQueryImporter(client.project)
            yield importer
