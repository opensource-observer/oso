import logging
import subprocess
import tempfile
from collections import deque
from pathlib import Path
from typing import Any, Dict, Generator

import dlt
import pandas as pd
from dagster import AssetExecutionContext, ResourceParam
from dlt.destinations.adapters import bigquery_adapter
from oso_dagster.config import DagsterConfig
from oso_dagster.factories import dlt_factory

logger = logging.getLogger(__name__)

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

            # Stream output in real-time, storing only last 100 lines for error context
            output_lines = deque(maxlen=100)
            if process.stdout:
                for line in process.stdout:
                    line_stripped = line.rstrip()
                    output_lines.append(line_stripped)
                    # Log every line to show progress
                    context.log.info(f"Download: {line_stripped}")

            # Wait with timeout (3 hours for 40GB download)
            # Increased timeout to handle large dataset downloads
            download_timeout = 10800  # 3 hours
            try:
                process.wait(timeout=download_timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                context.log.error(
                    f"Download command timed out after {download_timeout // 3600} hours"
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

                    # Read parquet file - pandas doesn't support chunksize for parquet
                    # Read entire file and process in chunks for memory efficiency
                    df = pd.read_parquet(parquet_file)
                    file_rows = len(df)
                    
                    # Add metadata columns to the dataframe before converting
                    df["_source_file"] = parquet_file.name
                    df["_source_table"] = table_name
                    df["_source_path"] = str(relative_path)
                    
                    # Convert to records (much faster than iterrows)
                    records = df.to_dict("records")
                    
                    # Explicitly delete dataframe to free memory
                    del df
                    
                    # Yield records with progress logging
                    rows_yielded = 0
                    for record in records:
                        # Ensure all keys are strings for type compatibility
                        # Column names from parquet should already be strings,
                        # but type checker requires explicit conversion
                        typed_record: Dict[str, Any] = {
                            str(k): v for k, v in record.items()
                        }
                        yield typed_record
                        rows_yielded += 1
                        
                        # Log progress every 100k rows for large files
                        if rows_yielded % 100000 == 0:
                            context.log.info(
                                f"File {file_idx}/{total_files}: Yielded {rows_yielded:,}/{file_rows:,} rows "
                                f"({rows_yielded / file_rows * 100:.1f}%)"
                            )
                    
                    # Explicitly delete records to free memory
                    del records

                    total_rows += file_rows

                    context.log.info(
                        f"File {file_idx}/{total_files}: Completed {parquet_file.name} "
                        f"({file_rows:,} rows) - Total processed so far: {total_rows:,} rows"
                    )

                except Exception as e:
                    context.log.warning(
                        f"Error processing file {parquet_file} ({file_idx}/{total_files}): {e}"
                    )
                    continue

            context.log.info(
                f"Finished processing all files. Total rows: {total_rows:,}"
            )

        except subprocess.CalledProcessError as e:
            context.log.error(f"Download command failed: {e}")
            # stderr was redirected to stdout, so log the captured output instead
            captured_output = getattr(e, "output", getattr(e, "stdout", None))
            if captured_output:
                context.log.error(f"Captured output: {captured_output}")
            raise
        except subprocess.TimeoutExpired:
            context.log.error("Download command timed out after 3 hours")
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
