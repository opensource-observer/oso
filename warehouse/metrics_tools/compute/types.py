import logging
import typing as t
from enum import Enum
from datetime import datetime

from metrics_tools.definition import PeerMetricDependencyRef
from pydantic import BaseModel
from sqlmesh.core.dialect import parse_one

logger = logging.getLogger(__name__)


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

    def query_as(self, dialect: str) -> str:
        return parse_one(self.query_str, self.dialect).sql(dialect=dialect)


class QueryJobSubmitResponse(BaseModel):
    job_id: str
    result_path: str


class QueryJobStatusResponse(BaseModel):
    job_id: str
    create_at: datetime
    update_at: datetime
    status: QueryJobStatus
    progress: QueryJobProgress


class QueryJobState(BaseModel):
    job_id: str
    created_at: datetime
    updates: t.List[QueryJobUpdate]

    def latest_update(self) -> QueryJobUpdate:
        return self.updates[-1]

    def as_response(self) -> QueryJobStatusResponse:
        return QueryJobStatusResponse(
            job_id=self.job_id,
            create_at=self.created_at,
            update_at=self.latest_update().updated_at,
            status=self.latest_update().status,
            progress=self.latest_update().progress,
        )


class ClusterStartRequest(BaseModel):
    min_size: int
    max_size: int


class ExportedTableLoad(BaseModel):
    map: t.Dict[str, str]
