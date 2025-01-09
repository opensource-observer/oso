"""Data transfer coordinator

This is not meant to be a full feature data transfer tool. We have most of that
figured out through things like dlt. However, there are instances where we need
to transfer between databases through gcs.
"""

import typing as t

from metrics_tools.compute.types import ExportType, TableReference
from metrics_tools.transfer.base import ExporterInterface, ImporterInterface
from pydantic import BaseModel


class Source(BaseModel):
    exporter: ExporterInterface
    table: TableReference


class Destination(BaseModel):
    importer: ImporterInterface
    table: TableReference

    def supported_types(self) -> t.Set[ExportType]:
        return self.importer.supported_types()


class DataTransferCoordinator:
    async def transfer(self, source: Source, destination: Destination):
        supported_types = destination.supported_types()
        export_reference = await source.exporter.export_table(
            source.table, supported_types
        )
        await destination.importer.import_table(export_reference)
