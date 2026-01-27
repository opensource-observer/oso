import uuid


def generate_uuid_as_bytes() -> bytes:
    """Generate a UUID and return it as bytes."""
    return uuid.uuid4().bytes
