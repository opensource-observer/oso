import pytest
from osoprotobufs.query_pb2 import QueryRunRequest
from scheduler.testing.handlers import (
    MessageHandlerTestHarness,
    message_handler_test_harness,
)
from scheduler.testing.uuids import generate_uuid_as_bytes

from .query import QueryRunRequestHandler


@pytest.fixture
def query_run_request_handler_harness():
    handler = QueryRunRequestHandler()
    harness = message_handler_test_harness(handler)
    yield harness


async def test_query_run_request_handler(
    query_run_request_handler_harness: MessageHandlerTestHarness,
):
    # Here you would create a QueryRunRequest message

    message = QueryRunRequest(
        run_id=generate_uuid_as_bytes(),
        query="SELECT * FROM test_table",
        user="test_user",
    )

    await query_run_request_handler_harness.send_message(message)
