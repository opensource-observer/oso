"""Data transfer coordinator

This is not meant to be a full feature data transfer tool. We have most of that
figured out through things like dlt. However, there are instances where we need
to transfer between databases through gcs.
"""

import logging
import typing as t
from dataclasses import dataclass

from metrics_service.types import ExportType, TableReference
from metrics_tools.transfer.base import ExporterInterface, ImporterInterface

module_logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class Source:
    exporter: ExporterInterface
    table: TableReference


@dataclass(kw_only=True)
class Destination:
    importer: ImporterInterface
    table: TableReference

    def supported_types(self) -> t.Set[ExportType]:
        return self.importer.supported_types()


async def transfer(
    source: Source,
    destination: Destination,
    log_override: t.Optional[logging.Logger] = None,
):
    logger = log_override or module_logger

    supported_types = destination.supported_types()
    logger.info(f"Exporting table {source.table.fqn}")
    export_reference = await source.exporter.export_table(source.table, supported_types)

    try:
        logger.info(f"Importing exported result into {destination.table.fqn}")
        await destination.importer.import_table(destination.table, export_reference)
    finally:
        logger.info("Cleaning up export reference")
        await source.exporter.cleanup_ref(export_reference)
