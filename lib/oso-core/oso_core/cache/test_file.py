import tempfile

import pytest
from pydantic import BaseModel

from .file import FileCacheBackend
from .types import CacheOptions


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
    cache = FileCacheBackend(cache_dir=temp_dir, default_options=CacheOptions(ttl=60))

    test0 = FakeModel(name="test", value=42)

    cache.store_object(key="test_key0", value=test0)
    stored_test0 = cache.retrieve_object(key="test_key0", model_type=FakeModel)

    assert test0 == stored_test0, "Stored and retrieved objects should match"
