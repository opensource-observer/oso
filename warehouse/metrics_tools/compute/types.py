import logging
import typing as t
from dataclasses import dataclass
from datetime import datetime

from metrics_tools.compute.cache import TrinoCacheExportManager
from metrics_tools.definition import PeerMetricDependencyRef
from pydantic import BaseModel
from sqlmesh.core.dialect import parse_one

from .cluster import ClusterManager

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class ApplicationState:
    id: str
    cluster_manager: ClusterManager
    cache_manager: TrinoCacheExportManager
    job_state: t.Dict[str, str]


class ClusterStatus(BaseModel):
    status: str
    is_ready: bool
    dashboard_url: str
    workers: int


class QueryJobSubmitInput(BaseModel):
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
    status: str


class ClusterStartRequest(BaseModel):
    min_size: int
    max_size: int
