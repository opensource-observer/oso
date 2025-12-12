import uuid

import structlog
from osoprotobufs.data_ingestion_pb2 import DataIngestionRunRequest
from scheduler.graphql_client.client import Client
from scheduler.types import MessageHandler

logger = structlog.getLogger(__name__)


def format_uuid_from_bytes(uuid_bytes: bytes) -> str:
    """Convert bytes to UUID string."""
    return str(uuid.UUID(bytes=uuid_bytes))


class DataIngestionRunRequestHandler(MessageHandler[DataIngestionRunRequest]):
    topic = "data_ingestion_run_requests"
    message_type = DataIngestionRunRequest
    schema_file_name = "data-ingestion.proto"

    async def handle_message(
        self,
        *,
        message: DataIngestionRunRequest,
        oso_client: Client,
        **_kwargs,
    ) -> None:
        run_id_bytes = bytes(message.run_id)
        config_id_bytes = bytes(message.config_id)
        dataset_id = message.dataset_id

        run_id = format_uuid_from_bytes(run_id_bytes)
        config_id = format_uuid_from_bytes(config_id_bytes)

        logger.info(
            "Received DataIngestionRunRequest",
            run_id=run_id,
            dataset_id=dataset_id,
            config_id=config_id,
        )

        _ = oso_client
