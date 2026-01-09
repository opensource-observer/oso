import asyncio
import uuid

from osoprotobufs.query_pb2 import QueryRunRequest
from scheduler.mq.common import RunHandler
from scheduler.types import CancelledResponse, HandlerResponse, SuccessResponse


class FakeWaitForeverRunRequestHandler(RunHandler[QueryRunRequest]):
    topic = "fake_wait_forever_run_requests"
    message_type = QueryRunRequest
    schema_file_name = "query.proto"

    async def handle_run_message(
        self,
        message: QueryRunRequest,
    ) -> HandlerResponse:
        # Process the QueryRunRequest message
        handler_id = uuid.uuid4()
        print("running fake wait forever handler")
        print(f"Handler ID: {handler_id} -- Message ID: {message.run_id}")
        try:
            while True:
                print("waiting...")
                await asyncio.sleep(15)
        except asyncio.CancelledError:
            print(f"Handler ID: {handler_id} -- Cancelled")
            return CancelledResponse()

        return SuccessResponse(
            message=f"Processed QueryRunRequest with ID: {message.run_id}"
        )
