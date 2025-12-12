import uuid


def convert_uuid_bytes_to_str(uuid_bytes: bytes) -> str:
    """Convert UUID bytes to a string representation."""

    return str(uuid.UUID(bytes=uuid_bytes))
