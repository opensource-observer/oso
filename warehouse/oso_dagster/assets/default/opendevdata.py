import logging
import subprocess
import tempfile
from collections import deque
from pathlib import Path
from typing import Any, Dict, Generator

import dlt
import pyarrow.parquet as pq
from dagster import AssetExecutionContext, ResourceParam
from dlt.destinations.adapters import bigquery_adapter
from oso_dagster.config import DagsterConfig
from oso_dagster.factories import dlt_factory

logger = logging.getLogger(__name__)

# Configuration constants
OUTPUT_BUFFER_LINES = 100  # Number of output lines to keep for error context
PARQUET_BATCH_SIZE = 100_000  # Batch size for parquet processing, balancing memory vs overhead
DOWNLOAD_TIMEOUT_SECONDS = 10800  # 3 hours for large dataset downloads

K8S_CONFIG = {
    "merge_behavior": "SHALLOW",
    "container_config": {
        "resources": {
            "requests": {"cpu": "2000m", "memory": "3584Mi"},
            "limits": {"memory": "7168Mi"},
        },
    },
}


def get_opendevdata_datasets(
    context: AssetExecutionContext,
) -> Generator[Dict[str, Any], None, None]:
    """
    Download and process Open Dev Data datasets using the CLI tools.

    This function uses the `uvx open-dev-data download` command to download
    parquet files, then reads and yields all datasets found.

    Args:
        context (AssetExecutionContext): The execution context

    Yields:
        Dict[str, Any]: Individual dataset records from all parquet files
    """
    # Create a temporary directory for downloading data
    with tempfile.TemporaryDirectory() as temp_dir:
        download_dir = Path(temp_dir) / "opendevdata"
        download_dir.mkdir(parents=True, exist_ok=True)

        try:
            context.log.info("Downloading Open Dev Data datasets using CLI")
            context.log.info(f"Download directory: {download_dir}")
            # Run the download command with streaming output
            process = subprocess.Popen(
                ["uvx", "open-dev-data", "download", "-o", str(download_dir)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # Stream output in real-time, storing only last N lines for error context
            output_lines = deque(maxlen=OUTPUT_BUFFER_LINES)
            if process.stdout:
                for line in process.stdout:
                    line_stripped = line.rstrip()
                    output_lines.append(line_stripped)
                    # Log every line to show progress
                    context.log.info(f"Download: {line_stripped}")

            # Wait with timeout
            try:
                process.wait(timeout=DOWNLOAD_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                context.log.error(
                    f"Download command timed out after {DOWNLOAD_TIMEOUT_SECONDS // 3600} hours"
                )
                raise

            if process.returncode != 0:
                error_output = "\n".join(output_lines)
                context.log.error(
                    f"Download command failed with return code {process.returncode}"
                )
                context.log.error(f"Output: {error_output}")
                raise subprocess.CalledProcessError(
                    process.returncode,
                    ["uvx", "open-dev-data", "download"],
                    output=error_output,
                )

            context.log.info("Download completed successfully")

            # Find all parquet files in the download directory
            parquet_files = list(download_dir.rglob("*.parquet"))
            context.log.info(f"Found {len(parquet_files)} parquet files")

            if not parquet_files:
                context.log.warning("No parquet files found after download")
                return

            # Process each parquet file
            total_files = len(parquet_files)
            total_rows = 0
            failed_files = []
            context.log.info(f"Starting to process {total_files} parquet files")

            for file_idx, parquet_file in enumerate(parquet_files, 1):
                try:
                    # Get file size for logging
                    file_size_mb = parquet_file.stat().st_size / (1024 * 1024)
                    relative_path = parquet_file.relative_to(download_dir)
                    table_name = (
                        str(relative_path).replace("/", "_").replace(".parquet", "")
                    )

                    context.log.info(
                        f"Processing file {file_idx}/{total_files}: {parquet_file.name} "
                        f"({file_size_mb:.2f} MB) - Table: {table_name}"
                    )

                    # Use pyarrow to read parquet file in batches for memory efficiency
                    parquet_file_obj = pq.ParquetFile(parquet_file)
                    file_rows = parquet_file_obj.metadata.num_rows
                    rows_yielded = 0

                    for batch in parquet_file_obj.iter_batches(batch_size=PARQUET_BATCH_SIZE):
                        # Convert batch directly to list of dicts for efficiency
                        batch_dict = batch.to_pydict()

                        # Add metadata columns to each column list
                        batch_dict["_source_file"] = [parquet_file.name] * len(batch)
                        batch_dict["_source_table"] = [table_name] * len(batch)
                        batch_dict["_source_path"] = [str(relative_path)] * len(batch)

                        # Convert to records by zipping column values
                        num_rows = len(batch)
                        for i in range(num_rows):
                            record = {key: values[i] for key, values in batch_dict.items()}
                            yield record
                            rows_yielded += 1

                        # Log progress every batch
                        if file_rows > 0:
                            percentage = (rows_yielded / file_rows * 100)
                            context.log.info(
                                f"File {file_idx}/{total_files}: Yielded {rows_yielded:,}/{file_rows:,} rows "
                                f"({percentage:.1f}%)"
                            )
                        else:
                            context.log.info(
                                f"File {file_idx}/{total_files}: Yielded {rows_yielded:,}/{file_rows:,} rows"
                            )

                    total_rows += file_rows

                    context.log.info(
                        f"File {file_idx}/{total_files}: Completed {parquet_file.name} "
                        f"({file_rows:,} rows) - Total processed so far: {total_rows:,} rows"
                    )

                except Exception as e:
                    context.log.warning(
                        f"Error processing file {parquet_file} ({file_idx}/{total_files}): {e}"
                    )
                    failed_files.append((parquet_file.name, str(e)))
                    continue

            # Log summary including any failures
            context.log.info(
                f"Finished processing all files. Total rows: {total_rows:,}"
            )
            if failed_files:
                context.log.warning(
                    f"Failed to process {len(failed_files)} file(s): "
                    f"{', '.join(f[0] for f in failed_files)}"
                )
                for filename, error in failed_files:
                    context.log.warning(f"  - {filename}: {error}")

        except subprocess.CalledProcessError as e:
            context.log.error(f"Download command failed: {e}")
            # stderr was redirected to stdout, so log the captured output instead
            captured_output = getattr(e, "output", getattr(e, "stdout", None))
            if captured_output:
                context.log.error(f"Captured output: {captured_output}")
            raise
        except Exception as e:
            context.log.error(f"Error processing Open Dev Data: {e}")
            raise


@dlt_factory(
    key_prefix="opendevdata",
    name="datasets",
    op_tags={
        "dagster/concurrency_key": "opendevdata_datasets",
        "dagster-k8s/config": K8S_CONFIG,
    },
)
def opendevdata_assets(
    context: AssetExecutionContext,
    global_config: ResourceParam[DagsterConfig],
):
    """
    Create and register a Dagster asset that materializes Open Dev Data datasets.

    This asset downloads parquet files using the Open Dev Data CLI and loads
    them into BigQuery.

    Args:
        context (AssetExecutionContext): The execution context of the asset.
        global_config (DagsterConfig): Global configuration parameters.

    Yields:
        Generator: A generator that yields Open Dev Data dataset records.
    """
    resource = dlt.resource(
        get_opendevdata_datasets(context),
        name="datasets",
        write_disposition="replace",
    )

    if global_config.gcp_bigquery_enabled:
        bigquery_adapter(
            resource,
            cluster=["_source_table"],
        )

    yield resource
