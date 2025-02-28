from contextlib import contextmanager
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from metrics_tools.compute.app import app_factory, default_lifecycle
from metrics_tools.compute.client import BaseWebsocketConnector, Client
from metrics_tools.compute.types import AppConfig
from metrics_tools.definition import PeerMetricDependencyRef
from metrics_tools.utils.logging import setup_module_logging
from starlette.testclient import WebSocketTestSession


@pytest.fixture
def app_client_with_all_debugging():
    setup_module_logging("metrics_tools")
    app = app_factory(
        default_lifecycle,
        AppConfig(
            cluster_namespace="namespace",
            cluster_service_account="service_account",
            cluster_name="name",
            worker_duckdb_path="path",
            trino_catalog="catalog",
            trino_host="trino",
            trino_user="trino",
            trino_port=8080,
            hive_catalog="catalog",
            hive_schema="schema",
            gcs_bucket="bucket",
            gcs_key_id="key",
            gcs_secret="secret",
            debug_all=True,
        ),
    )

    with TestClient(app) as client:
        yield client


class TestWebsocketConnector(BaseWebsocketConnector):
    def __init__(self, session: WebSocketTestSession):
        self.session = session

    def receive(self):
        return self.session.receive_text()

    def send(self, data: str):
        return self.session.send_text(data)


class TestClientWebsocketConnectFactory(BaseWebsocketConnector):
    def __init__(self, client: TestClient):
        self.client = client

    @contextmanager
    def __call__(self, *, base_url: str, path: str):
        with self.client.websocket_connect(path) as ws:
            yield TestWebsocketConnector(ws)


def test_app_with_all_debugging(app_client_with_all_debugging):
    client = Client(
        app_client_with_all_debugging,
        retries=1,
        websocket_connect_factory=TestClientWebsocketConnectFactory(
            app_client_with_all_debugging
        ),
    )

    start = "2021-01-01"
    end = "2021-01-03"
    batch_size = 1
    cluster_size = 1

    mock_handler = MagicMock()

    reference = client.calculate_metrics(
        query_str="""SELECT * FROM test""",
        start=datetime.strptime(start, "%Y-%m-%d"),
        end=datetime.strptime(end, "%Y-%m-%d"),
        dialect="duckdb",
        columns=[
            ("bucket_day", "TIMESTAMP"),
            ("to_artifact_id", "VARCHAR"),
            ("from_artifact_id", "VARCHAR"),
            ("event_source", "VARCHAR"),
            ("event_type", "VARCHAR"),
            ("amount", "NUMERIC"),
        ],
        ref=PeerMetricDependencyRef(
            name="",
            entity_type="artifact",
            window=30,
            unit="day",
            cron="@daily",
        ),
        locals={},
        dependent_tables_map={
            "metrics.events_daily_to_artifact": "sqlmesh__metrics.metrics__events_daily_to_artifact__2357434958"
        },
        slots=2,
        batch_size=batch_size,
        cluster_max_size=cluster_size,
        cluster_min_size=cluster_size,
        progress_handler=mock_handler,
    )

    # The pending to running update, and the 3 completion updates
    assert mock_handler.call_count == 4
    assert reference is not None
