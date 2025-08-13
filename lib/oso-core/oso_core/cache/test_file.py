import tempfile

import pytest
from pydantic import BaseModel

from .file import FileCacheBackend
from .types import CacheMetadataOptions


class FakeModel(BaseModel):
    """A simple Pydantic model for testing purposes."""

    name: str
    value: int


class FakeNestedModel(BaseModel):
    """A nested Pydantic model for testing purposes."""

    name: str
    nested: FakeModel


@pytest.fixture
def temp_dir():
    """Create a temporary directory for file system tests."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


def test_write_file_to_temp_dir(temp_dir):
    """Test writing a file to the temporary directory."""
    cache_backend = FileCacheBackend(cache_dir=temp_dir)

    test0 = FakeModel(name="test", value=42)

    options = CacheMetadataOptions(ttl_seconds=60)

    cache_backend.store_object(key="test_key0", value=test0, options=options)
    stored_test0 = cache_backend.retrieve_object(
        key="test_key0", model_type=FakeModel, options=options
    )

    assert test0 == stored_test0, "Stored and retrieved objects should match"

    test1 = FakeNestedModel(name="nested_test", nested=test0)
    cache_backend.store_object(key="test_key1", value=test1, options=options)
    stored_test1 = cache_backend.retrieve_object(
        key="test_key1", model_type=FakeNestedModel, options=options
    )
    assert test1 == stored_test1, "Nested stored and retrieved objects should match"
