import logging
import math
import typing as t
from datetime import datetime
from enum import Enum

import pandas as pd
from fastapi import FastAPI
from metrics_tools.definition import PeerMetricDependencyRef
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlmesh.core.dialect import parse_one

logger = logging.getLogger(__name__)


class EmptyResponse(BaseModel):
    type: t.Literal["EmptyResponse"] = "EmptyResponse"


class ExportType(str, Enum):
    ICEBERG = "iceberg"
    GCS = "gcs"
    TRINO = "trino"
    LOCALFS = "localfs"


DUCKDB_TO_PANDAS_TYPE_MAP = {
    "BOOLEAN": "bool",
    "BOOL": "bool",
    "TINYINT": "int8",
    "INT1": "int8",
    "SMALLINT": "int16",
    "INT2": "int16",
    "INTEGER": "int32",
    "INT4": "int32",
    "BIGINT": "int64",
    "INT8": "int64",
    "FLOAT": "float32",
    "FLOAT4": "float32",
    "DOUBLE": "float64",
    "FLOAT8": "float64",
    "DATE": "datetime64[ns]",
    "TIMESTAMP": "datetime64[ns]",
    "DATETIME": "datetime64[ns]",
    "VARCHAR": "object",
    "CHAR": "object",
    "BPCHAR": "object",
    "TEXT": "object",
    "BLOB": "bytes",
    "BYTEA": "bytes",
    "NUMERIC": "float64",
}


class ColumnsDefinition(BaseModel):
    columns: t.List[t.Tuple[str, str]]
    dialect: str = "duckdb"

    def columns_as(self, dialect: str) -> t.List[t.Tuple[str, str]]:
        return [
            (col_name, parse_one(col_type, dialect=self.dialect).sql(dialect=dialect))
            for col_name, col_type in self.columns
        ]

    def __iter__(self):
        for col_name, col_type in self.columns:
            yield (col_name, col_type)

    def to_pandas(self) -> pd.DataFrame:
        """Creates a basic dataframe with the columns defined in this definition
        coerced to panda datatypes"""
        columns_as_pandas_dtypes = self.columns_as_pandas_dtypes()
        df = pd.DataFrame({col_name: [] for col_name, _ in columns_as_pandas_dtypes})
        for col_name, col_type in columns_as_pandas_dtypes:
            df[col_name] = df[col_name].astype(col_type)  # type: ignore
        return df

    def columns_as_pandas_dtypes(self) -> t.List[t.Tuple[str, str]]:
        return [
            (col_name, DUCKDB_TO_PANDAS_TYPE_MAP[col_type.upper()])
            for col_name, col_type in self.columns_as("duckdb")
        ]


class TableReference(BaseModel):
    catalog_name: t.Optional[str] = None
    schema_name: t.Optional[str] = None
    table_name: str

    @property
    def fqn(self) -> str:
        names = []
        if self.catalog_name:
            names.append(self.catalog_name)
        if self.schema_name:
            names.append(self.schema_name)
        names.append(self.table_name)
        return ".".join(names)


class ExportReference(BaseModel):
    columns: ColumnsDefinition
    table: TableReference
    type: ExportType
    payload: t.Dict[str, t.Any]

    # Used to provide any additional metadata about the export by an exporter
    source_metadata: t.Dict[str, t.Any] = Field(default_factory=dict)

    def table_fqn(self):
        return self.table.fqn


class QueryJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class QueryJobTaskStatus(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    CANCELLED = "cancelled"
    FAILED = "failed"


class QueryJobUpdateScope(str, Enum):
    TASK = "task"
    JOB = "job"


class QueryJobProgress(BaseModel):
    completed: int
    total: int


class QueryJobTaskUpdate(BaseModel):
    type: t.Literal[QueryJobUpdateScope.TASK] = QueryJobUpdateScope.TASK
    status: QueryJobTaskStatus
    task_id: str
    exception: t.Optional[str] = None


class QueryJobStateUpdate(BaseModel):
    type: t.Literal[QueryJobUpdateScope.JOB] = QueryJobUpdateScope.JOB
    status: QueryJobStatus
    has_remaining_tasks: bool
    exception: t.Optional[str] = None


QueryJobUpdateTypes = t.Union[
    QueryJobTaskUpdate,
    QueryJobStateUpdate,
]


class QueryJobUpdate(BaseModel):
    time: datetime
    scope: QueryJobUpdateScope
    payload: QueryJobUpdateTypes = Field(discriminator="type")

    @classmethod
    def create_job_update(cls, payload: QueryJobStateUpdate) -> "QueryJobUpdate":
        return cls(time=datetime.now(), scope=QueryJobUpdateScope.JOB, payload=payload)

    @classmethod
    def create_task_update(cls, payload: QueryJobTaskUpdate) -> "QueryJobUpdate":
        return cls(time=datetime.now(), scope=QueryJobUpdateScope.TASK, payload=payload)


class ClusterStatus(BaseModel):
    status: str
    is_ready: bool
    dashboard_url: str
    workers: int


class ClusterStatusResponse(BaseModel):
    type: t.Literal["ClusterStatusResponse"] = "ClusterStatusResponse"
    status: ClusterStatus


class JobSubmitRequest(BaseModel):
    type: t.Literal["JobSubmitRequest"] = "JobSubmitRequest"
    query_str: str
    start: datetime
    end: datetime
    dialect: str
    batch_size: int
    columns: t.List[t.Tuple[str, str]]
    ref: PeerMetricDependencyRef
    locals: t.Dict[str, t.Any]
    dependent_tables_map: t.Dict[str, str]
    retries: t.Optional[int] = None
    slots: int = 2
    execution_time: datetime

    def query_as(self, dialect: str) -> str:
        return parse_one(self.query_str, self.dialect).sql(dialect=dialect)

    @property
    def columns_def(self) -> ColumnsDefinition:
        return ColumnsDefinition(columns=self.columns, dialect=self.dialect)

    def batch_count(self):
        """The expected number of batches for this job"

        This is calculated by getting the range (inclusive) between the start
        and end and dividing by the batch size.
        """
        inclusive_day_length = (self.end - self.start).days + 1
        return math.ceil(inclusive_day_length / self.batch_size)


class JobSubmitResponse(BaseModel):
    type: t.Literal["JobSubmitResponse"] = "JobSubmitResponse"
    job_id: str
    export_reference: ExportReference


class JobStatusResponse(BaseModel):
    type: t.Literal["JobStatusResponse"] = "JobStatusResponse"
    job_id: str
    created_at: datetime
    updated_at: datetime
    status: QueryJobStatus
    progress: QueryJobProgress
    stats: t.Dict[str, float] = Field(default_factory=dict)
    exceptions: t.List[str] = Field(default_factory=list)


class QueryJobState(BaseModel):
    job_id: str
    created_at: datetime
    tasks_count: int
    tasks_completed: int = 0
    has_remaining_tasks: bool = True
    status: QueryJobStatus = QueryJobStatus.PENDING
    updates: t.List[QueryJobUpdate]

    @classmethod
    def start(cls, job_id: str, tasks_count: int) -> "QueryJobState":
        now = datetime.now()
        return cls(
            job_id=job_id,
            created_at=now,
            tasks_count=tasks_count,
            updates=[
                QueryJobUpdate(
                    time=now,
                    scope=QueryJobUpdateScope.JOB,
                    payload=QueryJobStateUpdate(
                        status=QueryJobStatus.PENDING,
                        has_remaining_tasks=True,
                    ),
                )
            ],
        )

    def latest_update(self) -> QueryJobUpdate:
        return self.updates[-1]

    def update(self, update: QueryJobUpdate):
        """Add an update to the job state and change any relevant job state"""
        self.updates.append(update)
        if update.scope == QueryJobUpdateScope.JOB:
            payload = t.cast(QueryJobStateUpdate, update.payload)
            if payload.status == QueryJobStatus.COMPLETED:
                if self.status != QueryJobStatus.FAILED:
                    self.status = QueryJobStatus.COMPLETED
                self.has_remaining_tasks = False
            elif payload.status == QueryJobStatus.FAILED:
                self.has_remaining_tasks = payload.has_remaining_tasks
                self.status = payload.status
            elif payload.status == QueryJobStatus.RUNNING:
                self.status = payload.status
        else:
            payload = t.cast(QueryJobTaskUpdate, update.payload)
            if payload.status == QueryJobTaskStatus.FAILED:
                self.status = QueryJobStatus.FAILED
            elif payload.status == QueryJobTaskStatus.CANCELLED:
                self.status = QueryJobStatus.FAILED
            self.tasks_completed += 1

    def as_response(
        self, include_stats: bool = False, include_exceptions_count: int = 5
    ) -> JobStatusResponse:
        # Turn update events into stats
        stats = {}
        if include_stats:
            # Calculate the time between each status change
            pending_to_running = None
            running_to_completed = None
            running_to_failed = None

            for update in self.updates:
                match update.scope:
                    case QueryJobUpdateScope.JOB:
                        if update.payload.status == QueryJobStatus.RUNNING:
                            pending_to_running = update.time
                        elif update.payload.status == QueryJobStatus.COMPLETED:
                            running_to_completed = update.time
                        elif update.payload.status == QueryJobStatus.FAILED:
                            if running_to_failed is None:
                                running_to_failed = update.time
                    case QueryJobUpdateScope.TASK:
                        if update.payload.status == QueryJobTaskStatus.FAILED:
                            if running_to_failed is None:
                                running_to_failed = update.time
                        elif update.payload.status == QueryJobTaskStatus.CANCELLED:
                            if running_to_failed is None:
                                running_to_failed = update.time

            if pending_to_running:
                stats["pending_to_running_seconds"] = (
                    pending_to_running - self.created_at
                ).total_seconds()
            if running_to_completed:
                stats["running_to_completed_seconds"] = (
                    (running_to_completed - pending_to_running).total_seconds()
                    if pending_to_running
                    else None
                )
            if running_to_failed:
                stats["running_to_failed_seconds"] = (
                    (running_to_failed - pending_to_running).total_seconds()
                    if pending_to_running
                    else None
                )
        exceptions: t.List[str] = []
        if self.status == QueryJobStatus.FAILED:
            for update in reversed(self.updates):
                if update.scope == QueryJobUpdateScope.TASK:
                    payload = t.cast(QueryJobTaskUpdate, update.payload)
                    if payload.status == QueryJobTaskStatus.FAILED:
                        if payload.exception:
                            exceptions.append(payload.exception)
                else:
                    payload = t.cast(QueryJobStateUpdate, update.payload)
                    if payload.exception:
                        exceptions.append(payload.exception)
                if len(exceptions) >= include_exceptions_count:
                    break

        return JobStatusResponse(
            job_id=self.job_id,
            created_at=self.created_at,
            updated_at=self.latest_update().time,
            status=self.status,
            progress=QueryJobProgress(
                completed=self.tasks_completed,
                total=self.tasks_count,
            ),
            stats=stats,
            exceptions=exceptions,
        )


class ClusterStartRequest(BaseModel):
    type: t.Literal["ClusterStartRequest"] = "ClusterStartRequest"
    min_size: int
    max_size: int


class ClusterStatusRequest(BaseModel):
    type: t.Literal["ClusterStatusRequest"] = "ClusterStatusRequest"


class JobStatusRequest(BaseModel):
    type: t.Literal["JobStatusRequest"] = "JobStatusRequest"
    job_id: str
    include_stats: bool


class ExportedTableLoadRequest(BaseModel):
    type: t.Literal["ExportedTableLoadRequest"] = "ExportedTableLoadRequest"
    map: t.Dict[str, ExportReference]


class InspectCacheRequest(BaseModel):
    type: t.Literal["InspectCacheRequest"] = "InspectCacheRequest"


class InspectCacheResponse(BaseModel):
    type: t.Literal["InspectCacheResponse"] = "InspectCacheResponse"
    map: t.Dict[str, ExportReference]


class ErrorResponse(BaseModel):
    type: t.Literal["ErrorResponse"] = "ErrorResponse"
    message: str


ServiceRequestTypes = t.Union[
    ClusterStartRequest,
    ClusterStatusRequest,
    JobStatusRequest,
    ExportedTableLoadRequest,
]


class ServiceRequest(BaseModel):
    type: str
    request: ServiceRequestTypes = Field(discriminator="type")


ServiceResponseTypes = t.Union[
    ClusterStatusResponse,
    JobStatusResponse,
    EmptyResponse,
    InspectCacheResponse,
    ErrorResponse,
]


class ServiceResponse(BaseModel):
    type: str
    response: ServiceResponseTypes = Field(discriminator="type")


class ClusterConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="metrics_")

    cluster_namespace: str
    cluster_service_account: str
    cluster_name: str
    cluster_image_repo: str = "ghcr.io/opensource-observer/oso"
    cluster_image_tag: str = "latest"

    scheduler_memory_limit: str = "90000Mi"
    scheduler_memory_request: str = "85000Mi"
    scheduler_pool_type: str = "sqlmesh-scheduler"

    worker_resources: t.Dict[str, int] = Field(default_factory=lambda: {"slots": 32})
    worker_threads: int = 8
    worker_memory_limit: str = "90000Mi"
    worker_memory_request: str = "85000Mi"
    worker_pool_type: str = "sqlmesh-worker"
    worker_duckdb_path: str


class GCSConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="metrics_")

    gcs_bucket: str
    gcs_key_id: str
    gcs_secret: str


class TrinoCacheExportConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="metrics_")

    trino_host: str
    trino_port: int
    trino_user: str
    trino_catalog: str
    hive_catalog: str = "source"
    hive_schema: str = "export"


class AppConfig(ClusterConfig, TrinoCacheExportConfig, GCSConfig):
    model_config = SettingsConfigDict(env_prefix="metrics_")

    results_path_prefix: str = "mcs-results"

    debug_all: bool = False
    debug_with_duckdb: bool = False
    debug_cache: bool = False
    debug_cluster: bool = False
    debug_cluster_no_shutdown: bool = False

    cluster_shutdown_timeout: int = 180
    cluster_scale_down_timeout: int = 60

    @model_validator(mode="after")
    def handle_debugging(self):
        if self.debug_all:
            self.debug_cache = True
            self.debug_cluster = True
            self.debug_with_duckdb = True
        return self


AppLifespan = t.Callable[[FastAPI], t.Any]

ConfigType = t.TypeVar("ConfigType")

AppLifespanFactory = t.Callable[[ConfigType], AppLifespan]
