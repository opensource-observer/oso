import typing as t

import structlog
from oso_core.logging import BindableLogger
from scheduler.types import RunLoggerContainer, RunLoggerFactory


class FakeRunLoggerContainer(RunLoggerContainer):
    def __init__(self, run_id: str):
        self._run_id = run_id

    @property
    def logger(self) -> BindableLogger:
        return structlog.get_logger("scheduler.testing").bind(run_id=self._run_id)

    async def destination_uris(self) -> list[str]:
        return []


class FakeRunLoggerFactory(RunLoggerFactory):
    def create_logger_container(self, run_id: str, **kwargs: t.Any):
        return FakeRunLoggerContainer(run_id)
