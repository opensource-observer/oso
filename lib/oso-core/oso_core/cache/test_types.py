from .types import CacheMetadata


def test_metadata_is_valid():
    """Test that metadata is valid when created and not expired."""
    metadata = CacheMetadata(
        created_at="2024-01-01T00:00:00Z", valid_until="2024-01-01T00:01:00Z"
    )
    assert metadata.is_valid() is True
