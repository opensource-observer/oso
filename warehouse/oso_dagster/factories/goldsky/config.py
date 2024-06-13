import os
from typing import Optional, Callable, List, Sequence, TypeVar
from dataclasses import dataclass, field

from google.cloud.bigquery.schema import SchemaField
from dagster import AssetChecksDefinition, AssetsDefinition

T = TypeVar("T")
CheckFactory = Callable[[T, AssetsDefinition], List[AssetChecksDefinition]]


@dataclass(kw_only=True)
class GoldskyConfig:
    # This is the name of the asset within the goldsky directory path in gcs
    name: str
    key_prefix: Optional[str | Sequence[str]] = ""
    project_id: str
    source_name: str
    destination_table_name: str

    # Maximum number of objects we can load into a load job is 10000 so the
    # largest this can be is 10000.
    pointer_size: int = int(os.environ.get("GOLDSKY_CHECKPOINT_SIZE", "5000"))

    max_objects_to_load: int = 200_000

    destination_dataset_name: str = "oso_sources"
    destination_bucket_name: str = "oso-dataset-transfer-bucket"

    source_bucket_name: str = "oso-dataset-transfer-bucket"
    source_goldsky_dir: str = "goldsky"

    dask_worker_memory: str = "4096Mi"
    dask_scheduler_memory: str = "2560Mi"
    dask_image: str = "ghcr.io/opensource-observer/dagster-dask:distributed-test-10"
    dask_is_enabled: bool = False
    dask_bucket_key_id: str = ""
    dask_bucket_secret: str = ""

    # Allow 15 minute load table jobs
    load_table_timeout_seconds: float = 3600
    transform_timeout_seconds: float = 3600

    working_destination_dataset_name: str = "oso_raw_sources"
    working_destination_preload_path: str = "_temp"

    dedupe_model: str = "goldsky_dedupe.sql"
    dedupe_unique_column: str = "id"
    dedupe_order_column: str = "ingestion_time"
    merge_workers_model: str = "goldsky_merge_workers.sql"

    partition_column_name: str = ""
    partition_column_type: str = "DAY"
    partition_column_transform: Callable = lambda a: a

    schema_overrides: List[SchemaField] = field(default_factory=lambda: [])

    retention_files: int = 10000

    checks: List[CheckFactory["GoldskyConfig"]] = field(default_factory=lambda: [])

    @property
    def destination_table_fqn(self):
        return f"{self.project_id}.{self.destination_dataset_name}.{self.destination_table_name}"

    def worker_raw_table_fqdn(self, worker: str):
        return f"{self.project_id}.{self.working_destination_dataset_name}.{self.destination_table_name}_{worker}"

    def worker_deduped_table_fqdn(self, worker: str):
        return f"{self.project_id}.{self.working_destination_dataset_name}.{self.destination_table_name}_deduped_{worker}"
