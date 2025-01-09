import logging
from urllib.parse import urlparse

from clickhouse_connect.driver.client import Client
from metrics_tools.compute.types import ExportReference, ExportType
from metrics_tools.transfer.base import ImporterInterface
from oso_dagster.utils.clickhouse import create_table, import_data

logger = logging.getLogger(__name__)


class ClickhouseImporter(ImporterInterface):
    def __init__(self, ch: Client):
        self.ch = ch

    def supported_types(self):
        return {ExportType.GCS}

    async def import_table(
        self, export_reference: ExportReference, override_table_name: str = ""
    ):
        if export_reference.type != ExportType.GCS:
            raise NotImplementedError(
                f"Unsupported export type: {export_reference.type}"
            )
        gcs_path = export_reference.payload["gcs_path"]
        parsed_gcs_path = urlparse(gcs_path)
        gcs_bucket = parsed_gcs_path.netloc
        gcs_blob_path = parsed_gcs_path.path.strip("/")

        table_name = override_table_name or export_reference.table.table_name
        logger.debug(f"Creating table {table_name}")
        create_table(
            self.ch,
            table_name,
            export_reference.columns.columns_as("clickhouse"),
        )
        import_path = f"https://storage.googleapis.com/{gcs_bucket}/{gcs_blob_path}/*"
        logger.debug(f"Importing table {table_name} from {gcs_path}")
        import_data(
            self.ch,
            table_name,
            import_path,
            format="Parquet",
        )
