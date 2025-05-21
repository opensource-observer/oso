"""Metrics Calculation Service Client"""

import json
import logging
import time
import typing as t
from contextlib import contextmanager
from datetime import datetime
from urllib.parse import urljoin

import httpx
from metrics_service.types import (
    ClusterStartRequest,
    ClusterStatus,
    EmptyResponse,
    ExportedTableLoadRequest,
    ExportReference,
    InspectCacheResponse,
    JobStatusResponse,
    JobSubmitRequest,
    JobSubmitResponse,
    PingResponse,
    QueryJobStatus,
    ServiceResponse,
)
from metrics_tools.definition import MetricModelDefinition
from pydantic import BaseModel
from pydantic_core import to_jsonable_python
from websockets.sync.client import connect
from websockets.sync.connection import Connection

logger = logging.getLogger(__name__)


class ResponseObject[T](t.Protocol):
    def model_validate(self, obj: dict) -> T: ...


class BaseWebsocketConnector:
    def receive(self) -> str:
        raise NotImplementedError()

    def send(self, data: str):
        raise NotImplementedError()


class WebsocketConnectFactory(t.Protocol):
    def __call__(
        self, *, base_url: str, path: str
    ) -> t.ContextManager[BaseWebsocketConnector]: ...


class WebsocketsConnector(BaseWebsocketConnector):
    def __init__(self, connection: Connection):
        self.connection = connection

    def receive(self):
        data = self.connection.recv()
        if isinstance(data, str):
            return data
        else:
            return data.decode()

    def send(self, data: str):
        return self.connection.send(data)


class ClientRetriesExceeded(Exception):
    pass


@contextmanager
def default_ws(*, base_url: str, path: str):
    url = urljoin(base_url, path)
    with connect(url) as ws:
        yield WebsocketsConnector(ws)


class Client:
    """A metrics calculation service client"""

    url: httpx.Client
    logger: logging.Logger

    @classmethod
    def from_url(
        cls,
        url: str,
        retries: int = 5,
        log_override: t.Optional[logging.Logger] = None,
    ):
        """Create a client from a base url

        Args:
            url (str): The base url
            retries (int): The number of retries the client should attempt when connecting
            log_override (t.Optional[logging.Logger]): An optional logger override

        Returns:
            Client: The client instance
        """
        return cls(
            httpx.Client(base_url=url),
            retries,
            default_ws,
            log_override=log_override,
        )

    def __init__(
        self,
        client: httpx.Client,
        retries: int,
        websocket_connect_factory: WebsocketConnectFactory,
        log_override: t.Optional[logging.Logger] = None,
    ):
        self.client = client
        self.retries = retries
        self.websocket_connect_factory = websocket_connect_factory
        self.logger = log_override or logger

    def calculate_metrics(
        self,
        *,
        query_str: str,
        start: datetime,
        end: datetime,
        dialect: str,
        batch_size: int,
        columns: t.List[t.Tuple[str, str]],
        ref: MetricModelDefinition,
        locals: t.Dict[str, t.Any],
        dependent_tables_map: t.Dict[str, str],
        slots: int,
        progress_handler: t.Optional[t.Callable[[JobStatusResponse], None]] = None,
        cluster_min_size: int = 6,
        cluster_max_size: int = 6,
        job_retries: int = 3,
        do_not_raise_on_failure: bool = False,
        execution_time: t.Optional[datetime] = None,
    ):
        """Calculate metrics for a given period and write the results to a gcs
        folder. This method is a high level method that triggers all of the
        necessary calls to complete a metrics calculation. Namely:

        1. Tell the metrics calculation service to start a compute cluster
        2. Submit a job to the service
        3. Wait for the job to complete (and log progress)
        4. Return the gcs result path

        If do_not_raise_on_failure is set to True, the method will not raise an
        exception on failure. This is done to ensure that this metrics calculation
        doesn't block the rest of the pipeline. Instead, sqlmesh should be called
        againt to restate the failed metrics calculations.

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
            job_retries (int): The number of retries for a given job in the
                worker queue. Defaults to 3.
            slots (int): The number of slots to use for the job
            do_not_raise_on_failure (bool): If true, the method will not raise
                an exception on failure. Instead an error will be logged and
                it'll be up to the caller to handle restatement of the metric.
            execution_time (t.Optional[datetime]): The execution time for the job

        Returns:
            ExportReference: The export reference for the resulting calculation
        """
        # Trigger the cluster start
        status = self.start_cluster(
            min_size=cluster_min_size, max_size=cluster_max_size
        )
        self.logger.info(f"cluster status: {status}")

        job_response = self.submit_job(
            query_str=query_str,
            start=start,
            end=end,
            dialect=dialect,
            batch_size=batch_size,
            columns=columns,
            ref=ref,
            locals=locals,
            dependent_tables_map=dependent_tables_map,
            slots=slots,
            job_retries=job_retries,
            execution_time=execution_time,
        )
        job_id = job_response.job_id
        export_reference = job_response.export_reference

        if not progress_handler:

            def _handler(response: JobStatusResponse):
                self.logger.info(
                    f"job[{job_id}] status: {response.status}, progress: {response.progress}"
                )

            progress_handler = _handler

        # Wait for the job to be completed
        final_status = self.wait_for_job(job_id, progress_handler)

        if final_status.status == QueryJobStatus.FAILED:
            self.logger.error(f"job[{job_id}] failed with status {final_status.status}")
            if final_status.exceptions:
                self.logger.error(f"job[{job_id}] failed with exceptions")

            for exc in final_status.exceptions:
                self.logger.error(f"job[{job_id}] failed with exceptoin {exc}")

            if not do_not_raise_on_failure:
                raise Exception(
                    f"job[{job_id}] failed with status {final_status.status}"
                )
            else:
                self.logger.error(
                    f"""
                    job[{job_id}] failed. To restate use the following parameters: 
                    `--restate-model {ref['name']} --start {start} --end {end}`
                """
                )
                return None

        self.logger.info(f"job[{job_id}] completed with status {final_status.status}")

        return export_reference

    def start_cluster(self, min_size: int, max_size: int):
        """Start a compute cluster with the given min and max size"""
        request = ClusterStartRequest(min_size=min_size, max_size=max_size)
        response = self.service_post_with_input(
            ClusterStatus, "/cluster/start", request
        )
        return response

    def wait_for_job(
        self, job_id: str, progress_handler: t.Callable[[JobStatusResponse], None]
    ):
        """Connect to the websocket and listen for job updates"""
        url = self.client.base_url
        with self.websocket_connect_factory(
            base_url=f"{url.copy_with(scheme="ws")}", path=f"/job/status/{job_id}/ws"
        ) as ws:
            while True:
                raw_res = ws.receive()
                res = ServiceResponse(response=json.loads(raw_res))
                match res.response:
                    case JobStatusResponse(status=status):
                        if status not in [
                            QueryJobStatus.PENDING,
                            QueryJobStatus.RUNNING,
                        ]:
                            return res.response
                        progress_handler(res.response)
                    case PingResponse():
                        continue

    def submit_job(
        self,
        *,
        query_str: str,
        start: datetime,
        end: datetime,
        dialect: str,
        batch_size: int,
        columns: t.List[t.Tuple[str, str]],
        ref: MetricModelDefinition,
        locals: t.Dict[str, t.Any],
        dependent_tables_map: t.Dict[str, str],
        slots: int,
        job_retries: t.Optional[int] = None,
        execution_time: t.Optional[datetime] = None,
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
            slots (int): The number of slots to use for the job
            job_retries (int): The number of retries for a given job in the worker queue. Defaults to 3.

        Returns:
            QueryJobSubmitResponse: The job response from the metrics calculation service
        """
        request = JobSubmitRequest(
            query_str=query_str,
            start=start,
            end=end,
            dialect=dialect,
            batch_size=batch_size,
            columns=columns,
            ref=ref,
            locals=locals,
            dependent_tables_map=dependent_tables_map,
            slots=slots,
            retries=job_retries,
            execution_time=execution_time or datetime.now(),
        )
        job_response = self.service_post_with_input(
            JobSubmitResponse, "/job/submit", request
        )
        return job_response

    def get_job_status(self, job_id: str):
        """Get the status of a job"""
        return self.service_get(JobStatusResponse, f"/job/status/{job_id}")

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
    ](
        self,
        method: str,
        factory: ResponseObject[T],
        path: str,
        client_retries: t.Optional[int] = None,
        **kwargs,
    ) -> T:
        def make_request():
            return self.client.request(
                method,
                path,
                **kwargs,
            )

        def retry_request(retries: int):
            for i in range(retries):
                try:
                    response = make_request()
                    response.raise_for_status()
                    return response
                except httpx.NetworkError as e:
                    self.logger.error(f"Failed request with network error, {e}")
                except httpx.TimeoutException as e:
                    self.logger.error(f"Failed request with timeout, {e}")
                except httpx.HTTPStatusError as e:
                    self.logger.error(
                        f"Failed request with response code: {e.response.status_code}"
                    )
                    if e.response.status_code >= 500:
                        self.logger.debug("server error, retrying")
                    elif e.response.status_code == 408:
                        self.logger.debug("request timeout, retrying")
                    else:
                        raise e
                time.sleep(2**i)  # Exponential backoff
            raise ClientRetriesExceeded("Request failed after too many retries")

        client_retries = client_retries or self.retries
        response = retry_request(client_retries)
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
