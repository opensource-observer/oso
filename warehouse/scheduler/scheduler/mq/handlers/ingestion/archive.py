import asyncio
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from dlt import pipeline
from pydantic import BaseModel, Field, ValidationError
from scheduler.config import CommonSettings
from scheduler.dlt_destination import DLTDestinationResource
from scheduler.mq.handlers.ingestion.base import IngestionHandler
from scheduler.mq.handlers.ingestion.utils import FileFormat, file_from_https
from scheduler.types import (
    FailedResponse,
    HandlerResponse,
    RunContext,
    StepContext,
    SuccessResponse,
)
from scheduler.utils import dlt_to_oso_schema

WriteDisposition = Literal["append", "replace"]


class SourceFile(BaseModel):
    """Configuration for a single source file."""

    url: str = Field(description="HTTPS URL to the file")
    format: FileFormat = Field(description="File format: parquet, csv, or json")


class ArchiveConfig(BaseModel):
    """Configuration for archive-based data ingestion."""

    sources: list[SourceFile] = Field(
        description="List of source files with their formats"
    )
    write_disposition: WriteDisposition = Field(
        default="replace",
        description=(
            "Write disposition for DLT pipeline. "
            "Only 'append' and 'replace' are supported for now"
        ),
    )


class ArchiveIngestionHandler(IngestionHandler):
    """Handler for archive-based data ingestion from HTTPS URLs."""

    async def execute(
        self,
        context: RunContext,
        step_context: StepContext,
        config: dict[str, object],
        dataset_id: str,
        org_id: str,
        destination_user: str,
        dlt_destination: DLTDestinationResource,
        common_settings: CommonSettings,
    ) -> HandlerResponse:
        """Execute archive data ingestion using DLT.

        Downloads files from HTTPS URLs and ingests them into the warehouse
        using DLT pipelines. Supports parquet, CSV, and JSON formats.

        Args:
            context: The run context
            step_context: The step context for logging and materialization
            config: The archive configuration dictionary
            dataset_id: The dataset ID
            org_id: The organization ID
            dlt_destination: DLT destination resource (Trino or DuckDB)
            common_settings: Common settings

        Returns:
            HandlerResponse indicating success or failure
        """
        try:
            archive_config = ArchiveConfig.model_validate(config)
        except ValidationError as e:
            step_context.log.error(
                "Invalid archive config", extra={"errors": e.errors()}
            )
            return FailedResponse(message="Invalid archive config")

        if not archive_config.sources:
            step_context.log.error("No source files provided")
            return FailedResponse(message="No source files provided")

        step_context.log.info(
            "Starting archive ingestion with DLT",
            extra={
                "dataset_id": dataset_id,
                "num_files": len(archive_config.sources),
                "sources": [
                    {"url": s.url, "format": s.format} for s in archive_config.sources
                ],
                "write_disposition": archive_config.write_disposition,
            },
        )

        catalog = common_settings.warehouse_shared_catalog_name
        dataset_schema = f"{org_id}_{dataset_id}".replace("-", "_")

        dlt_resources = []
        for source in archive_config.sources:
            step_context.log.info(f"Creating DLT resource for: {source.url}")

            filename = Path(urlparse(source.url).path).stem
            table_name = f"data_ingestion_{filename}".replace("-", "_")

            step_context.log.info(
                "Creating HTTPS file resource",
                extra={
                    "url": source.url,
                    "format": source.format,
                    "table_name": table_name,
                },
            )

            resource = file_from_https(
                source.url,
                file_format=source.format,
                batch_size=50000,
                timeout=600,
            ).with_name(table_name)

            dlt_resources.append(resource)

        pipeline_name = f"archive_{org_id}_{dataset_id}".replace("-", "")[:50]

        try:
            async with dlt_destination.get_destination(
                dataset_schema=dataset_schema,
                user=destination_user,
            ) as destination:
                dlt_pipeline = pipeline(
                    pipeline_name=pipeline_name,
                    dataset_name=dataset_schema,
                    destination=destination,
                    pipelines_dir=common_settings.local_working_dir,
                )

                step_context.log.info(
                    "Running DLT pipeline",
                    extra={
                        "pipeline_name": pipeline_name,
                        "dataset_schema": dataset_schema,
                    },
                )

                load_info = await asyncio.to_thread(
                    dlt_pipeline.run,
                    dlt_resources,
                    write_disposition=archive_config.write_disposition,
                )

                step_context.log.info(
                    "DLT pipeline completed",
                    extra={
                        "load_packages": len(load_info.load_packages),
                        "dataset_name": load_info.dataset_name,
                    },
                )

            tables = dlt_pipeline.default_schema.data_tables()

            step_context.log.info(
                f"Extracted {len(tables)} tables from DLT schema",
                extra={"table_names": [t.get("name") for t in tables]},
            )

            for table in tables:
                table_name = table.get("name")
                if not table_name:
                    step_context.log.warning(
                        "Skipping table without name",
                        extra={"table": table},
                    )
                    continue

                oso_schema = dlt_to_oso_schema(table.get("columns", {}))
                warehouse_fqn = f"{catalog}.{dataset_schema}.{table_name}"

                step_context.log.info(
                    "Creating materialization",
                    extra={
                        "table_name": table_name,
                        "warehouse_fqn": warehouse_fqn,
                        "num_columns": len(oso_schema),
                    },
                )

                await step_context.create_materialization(
                    table_id=table_name,
                    warehouse_fqn=warehouse_fqn,
                    schema=oso_schema,
                )

            step_context.log.info(
                "Archive ingestion completed successfully",
                extra={
                    "dataset_id": dataset_id,
                    "num_files": len(archive_config.sources),
                    "num_tables": len(tables),
                },
            )

            return SuccessResponse(message="Archive ingestion completed successfully")

        except Exception as e:
            step_context.log.error(
                "Archive ingestion failed",
                extra={"error": str(e)},
                exc_info=True,
            )
            return FailedResponse(message=f"Archive ingestion failed: {e}")
