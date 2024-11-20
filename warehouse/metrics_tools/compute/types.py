import logging
import typing as t
from enum import Enum
from datetime import datetime

from metrics_tools.definition import PeerMetricDependencyRef
from pydantic import BaseModel, Field
from sqlmesh.core.dialect import parse_one

logger = logging.getLogger(__name__)


class EmptyResponse(BaseModel):
    pass


class ExportType(str, Enum):
    ICEBERG = "iceberg"
    GCS = "gcs"


class ExportReference(BaseModel):
    table: str
    type: ExportType
    payload: t.Dict[str, t.Any]


class QueryJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class QueryJobProgress(BaseModel):
    completed: int
    total: int


class QueryJobUpdate(BaseModel):
    updated_at: datetime
    status: QueryJobStatus
    progress: QueryJobProgress


class ClusterStatus(BaseModel):
    status: str
    is_ready: bool
    dashboard_url: str
    workers: int


class QueryJobSubmitRequest(BaseModel):
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

    def query_as(self, dialect: str) -> str:
        return parse_one(self.query_str, self.dialect).sql(dialect=dialect)


class QueryJobSubmitResponse(BaseModel):
    job_id: str
    result_path: str


class QueryJobStatusResponse(BaseModel):
    job_id: str
    created_at: datetime
    updated_at: datetime
    status: QueryJobStatus
    progress: QueryJobProgress
    stats: t.Dict[str, float] = Field(default_factory=dict)


class QueryJobState(BaseModel):
    job_id: str
    created_at: datetime
    updates: t.List[QueryJobUpdate]

    def latest_update(self) -> QueryJobUpdate:
        return self.updates[-1]

    def as_response(self, include_stats: bool = False) -> QueryJobStatusResponse:
        # Turn update events into stats
        stats = {}
        if include_stats:
            # Calculate the time between each status change
            pending_to_running = None
            running_to_completed = None
            running_to_failed = None

            for update in self.updates:
                if (
                    update.status == QueryJobStatus.RUNNING
                    and pending_to_running is None
                ):
                    pending_to_running = update.updated_at
                elif (
                    update.status == QueryJobStatus.COMPLETED
                    and running_to_completed is None
                ):
                    running_to_completed = update.updated_at
                elif (
                    update.status == QueryJobStatus.FAILED and running_to_failed is None
                ):
                    running_to_failed = update.updated_at

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

        return QueryJobStatusResponse(
            job_id=self.job_id,
            created_at=self.created_at,
            updated_at=self.latest_update().updated_at,
            status=self.latest_update().status,
            progress=self.latest_update().progress,
            stats=stats,
        )


class ClusterStartRequest(BaseModel):
    min_size: int
    max_size: int


class ExportedTableLoadRequest(BaseModel):
    map: t.Dict[str, ExportReference]


class InspectCacheResponse(BaseModel):
    map: t.Dict[str, ExportReference]
