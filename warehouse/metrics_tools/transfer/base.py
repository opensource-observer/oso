import typing as t
from datetime import datetime

from metrics_service.types import ExportReference, ExportType, TableReference


class ExporterInterface(t.Protocol):
    async def export_table(
        self, table: TableReference, supported_types: t.Set[ExportType]
    ) -> ExportReference: ...

    async def cleanup_ref(self, export_reference: ExportReference): ...

    async def cleanup_expired(self, expiration: datetime): ...


class ImporterInterface(t.Protocol):
    def supported_types(self) -> t.Set[ExportType]: ...

    async def import_table(
        self, destination_table: TableReference, export_reference: ExportReference
    ): ...


class Exporter(ExporterInterface):
    async def export_table(
        self, table: TableReference, supported_types: t.Set[ExportType]
    ) -> ExportReference:
        raise NotImplementedError("export_table not implemented")

    async def cleanup_ref(self, export_reference: ExportReference):
        raise NotImplementedError("cleanup_ref not implemented")

    async def cleanup_expired(self, expiration: datetime):
        raise NotImplementedError("cleanup_expired not implemented")


class Importer(ImporterInterface):
    def supported_types(self) -> t.Set[ExportType]:
        raise NotImplementedError("Not implemented")

    async def import_table(
        self, destination_table: TableReference, export_reference: ExportReference
    ):
        raise NotImplementedError("Not implemented")
