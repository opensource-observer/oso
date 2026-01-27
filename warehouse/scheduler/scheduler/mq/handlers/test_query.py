import pytest
from osoprotobufs.query_pb2 import QueryRunRequest
from scheduler.testing.handlers import (
    MessageHandlerTestHarness,
    default_message_handler_test_harness,
)
from scheduler.testing.resources.gcs import FakeGCSFileResource
from scheduler.testing.resources.trino import FakeTrinoResource
from scheduler.testing.uuids import generate_uuid_as_bytes
from scheduler.types import SuccessResponse

from .query import QueryRunRequestHandler


@pytest.fixture
def fake_trino_resource():
    yield FakeTrinoResource.create()


@pytest.fixture
def fake_gcs_resource():
    yield FakeGCSFileResource("test_project")


@pytest.fixture
def query_run_request_handler_harness(
    fake_trino_resource: FakeTrinoResource, fake_gcs_resource: FakeGCSFileResource
):
    handler = QueryRunRequestHandler()
    harness = default_message_handler_test_harness(
        handler,
        additional_resources=[
            ("consumer_trino", fake_trino_resource),
            ("gcs", fake_gcs_resource),
        ],
    )
    yield harness


@pytest.mark.medium
@pytest.mark.asyncio
async def test_query_run_request_handler(
    query_run_request_handler_harness: MessageHandlerTestHarness,
):
    # Here you would create a QueryRunRequest message

    message = QueryRunRequest(
        run_id=generate_uuid_as_bytes(),
        query="SELECT * FROM test_table",
        user="test_user",
    )

    response = await query_run_request_handler_harness.send_message(message)
    assert isinstance(response, SuccessResponse), (
        f"expected a SuccessResponse not {type(response)} - {response.message}"
    )
