"""A client for user defined models (UDM)."""

import logging
import typing as t
from contextlib import asynccontextmanager

import dagster as dg
from scheduler.types import UserDefinedModelStateClient

module_logger = logging.getLogger(__name__)


class UserDefinedModelStateResource(dg.ConfigurableResource):
    """Base UDM resource"""

    @asynccontextmanager
    def get_client(
        self,
    ) -> t.AsyncIterator[UserDefinedModelStateClient]:
        raise NotImplementedError(
            "get_client not implemented on the base UserDefinedModelClientResource"
        )


class FakeUserDefinedModelResource(UserDefinedModelStateResource):
    """A fake UDM resource for testing purposes."""

    @asynccontextmanager
    async def get_client(
        self,
    ) -> t.AsyncIterator[UserDefinedModelStateClient]:
        from scheduler.testing.client import FakeUDMClient

        yield FakeUDMClient()
