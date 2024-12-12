"""Metrics Calculation Service Client"""

import logging
import time
import typing as t
from datetime import datetime

import requests
from metrics_tools.compute.types import (
    ClusterStartRequest,
    ClusterStatus,
    EmptyResponse,
    ExportedTableLoadRequest,
    ExportReference,
    InspectCacheResponse,
    QueryJobStatus,
    QueryJobStatusResponse,
    QueryJobSubmitRequest,
    QueryJobSubmitResponse,
)
from metrics_tools.definition import PeerMetricDependencyRef
from pydantic import BaseModel
from pydantic_core import to_jsonable_python

logger = logging.getLogger(__name__)


class ResponseObject[T](t.Protocol):
    def model_validate(self, obj: dict) -> T: ...


class Client:
    """A metrics calculation service client"""

    url: str
    logger: logging.Logger

    def __init__(self, url: str, log_override: t.Optional[logging.Logger] = None):
        self.url = url
        self.logger = log_override or logger

    def calculate_metrics(
        self,
        query_str: str,
        start: datetime,
        end: datetime,
        dialect: str,
        batch_size: int,
        columns: t.List[t.Tuple[str, str]],
        ref: PeerMetricDependencyRef,
        locals: t.Dict[str, t.Any],
        dependent_tables_map: t.Dict[str, str],
        cluster_min_size: int = 6,
        cluster_max_size: int = 6,
        retries: t.Optional[int] = None,
    ):
        """Calculate metrics for a given period and write the results to a gcs
        folder. This method is a high level method that triggers all of the
        necessary calls to complete a metrics calculation. Namely:

        1. Tell the metrics calculation service to start a compute cluster
        2. Submit a job to the service
        3. Wait for the job to complete (and log progress)
        4. Return the gcs result path

        Args:
            query_str (str): The query to execute
            start (datetime): The start date
            end (datetime): The end date
            dialect (str): The sql dialect for the provided query
            batch_size (int): The batch size
            columns (t.List[t.Tuple[str, str]]): The columns to expect
            ref (PeerMetricDependencyRef): The dependency reference
            locals (t.Dict[str, t.Any]): The local variables to use
            dependent_tables_map (t.Dict[str, str]): The dependent tables map
            retries (t.Optional[int], optional): The number of retries. Defaults to None.

        Returns:
            ExportReference: The export reference for the resulting calculation
        """
        # Trigger the cluster start
        status = self.start_cluster(
            min_size=cluster_min_size, max_size=cluster_max_size
        )
        self.logger.info(f"cluster status: {status}")

        job_response = self.submit_job(
            query_str,
            start,
            end,
            dialect,
            batch_size,
            columns,
            ref,
            locals,
            dependent_tables_map,
            retries,
        )
        job_id = job_response.job_id
        export_reference = job_response.export_reference

        # Wait for the job to be completed
        status_response = self.get_job_status(job_id)
        while status_response.status in [
            QueryJobStatus.PENDING,
            QueryJobStatus.RUNNING,
        ]:
            self.logger.info(f"job[{job_id}] is still pending")
            status_response = self.get_job_status(job_id)
            time.sleep(5)
            self.logger.info(f"job[{job_id}] status is {status_response}")

        if status_response.status == QueryJobStatus.FAILED:
            self.logger.error(
                f"job[{job_id}] failed with status {status_response.status}"
            )
            raise Exception(
                f"job[{job_id}] failed with status {status_response.status}"
            )

        self.logger.info(
            f"job[{job_id}] completed with status {status_response.status}"
        )

        return export_reference

    def start_cluster(self, min_size: int, max_size: int):
        """Start a compute cluster with the given min and max size"""
        request = ClusterStartRequest(min_size=min_size, max_size=max_size)
        response = self.service_post_with_input(
            ClusterStatus, "/cluster/start", request
        )
        return response

    def submit_job(
        self,
        query_str: str,
        start: datetime,
        end: datetime,
        dialect: str,
        batch_size: int,
        columns: t.List[t.Tuple[str, str]],
        ref: PeerMetricDependencyRef,
        locals: t.Dict[str, t.Any],
        dependent_tables_map: t.Dict[str, str],
        retries: t.Optional[int] = None,
    ):
        """Submit a job to the metrics calculation service

        Args:
            query_str (str): The query to execute
            start (datetime): The start date
            end (datetime): The end date
            dialect (str): The sql dialect for the provided query
            batch_size (int): The batch size
            columns (t.List[t.Tuple[str, str]]): The columns to expect
            ref (PeerMetricDependencyRef): The dependency reference
            locals (t.Dict[str, t.Any]): The local variables to use
            dependent_tables_map (t.Dict[str, str]): The dependent tables map
            retries (t.Optional[int], optional): The number of retries. Defaults to None.

        Returns:
            QueryJobSubmitResponse: The job response from the metrics calculation service
        """
        request = QueryJobSubmitRequest(
            query_str=query_str,
            start=start,
            end=end,
            dialect=dialect,
            batch_size=batch_size,
            columns=columns,
            ref=ref,
            locals=locals,
            dependent_tables_map=dependent_tables_map,
            retries=retries,
            execution_time=datetime.now(),
        )
        job_response = self.service_post_with_input(
            QueryJobSubmitResponse, "/job/submit", request
        )
        return job_response

    def get_job_status(self, job_id: str):
        """Get the status of a job"""
        return self.service_get(QueryJobStatusResponse, f"/job/status/{job_id}")

    def run_cache_manual_load(self, map: t.Dict[str, ExportReference]):
        """Load a cache with the provided map. This is useful for testing
        purposes but generally shouldn't be used in production"""
        req = ExportedTableLoadRequest(map=map)
        return self.service_post_with_input(EmptyResponse, "/cache/manual", req)

    def inspect_cache(self):
        """Inspect the cached export tables for the service"""
        return self.service_get(InspectCacheResponse, "/cache/inspect")

    def service_request[
        T
    ](self, method: str, factory: ResponseObject[T], path: str, **kwargs) -> T:
        response = requests.request(
            method,
            f"{self.url}{path}",
            **kwargs,
        )
        return factory.model_validate(response.json())

    def service_post_with_input[
        T
    ](
        self,
        factory: ResponseObject[T],
        path: str,
        input: BaseModel,
        params: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> T:
        return self.service_request(
            "POST",
            factory,
            path,
            json=to_jsonable_python(input),
            params=params,
        )

    def service_get[
        T
    ](
        self,
        factory: ResponseObject[T],
        path: str,
        params: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> T:
        return self.service_request(
            "GET",
            factory,
            path,
            params=params,
        )
