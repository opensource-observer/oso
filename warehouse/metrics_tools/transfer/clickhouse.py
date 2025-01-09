from clickhouse_connect.driver.client import Client
from metrics_tools.compute.types import ExportReference, ExportType
from metrics_tools.transfer.base import ImporterInterface


class ClickhouseImporter(ImporterInterface):
    def __init__(self, ch: Client):
        self.ch = ch

    def supported_types(self):
        return {ExportType.GCS}

    async def import_table(self, export_reference: ExportReference):
        pass
