import arrow

from .types import CacheMetadata


def test_metadata_is_valid():
    """Test that metadata is valid when created and not expired."""
    now = arrow.now()

    created_at = now.shift(seconds=-60)
    valid_until = now.shift(seconds=60)
    metadata = CacheMetadata(
        created_at=created_at.isoformat(), valid_until=valid_until.isoformat()
    )
    assert metadata.is_valid() is True
