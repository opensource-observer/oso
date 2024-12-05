"""Wraps the sqlmesh controller from dagster sqlmesh to provide a richer
experience specifically for creating metrics models"""

import logging
import os
import typing as t

from dagster_sqlmesh.config import SQLMeshContextConfig
from dagster_sqlmesh.controller.base import SQLMeshController


class MetricsController:
    @classmethod
    def setup(
        cls,
        path: str,
        environment: str = "test",
        gateway: str = "local",
        enable_logging: bool = False,
        log_override: t.Optional[logging.Logger] = None,
    ):
        if enable_logging:
            import sys

            logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        config = SQLMeshContextConfig(path=path, gateway=gateway)
        controller = SQLMeshController.setup(
            config,
            log_override=log_override,
        )
        os.environ["SQLMESH_TIMESERIES_METRICS_START"] = "2024-07-01"
        return cls(environment, controller)

    def __init__(self, environment: str, sqlmesh_controller: SQLMeshController):
        self._environment = environment
        self._sqlmesh_controller = sqlmesh_controller

    def load(self):
        # Debug console
        for context, event in self._sqlmesh_controller.plan(
            environment=self._environment,
            skip_tests=True,
        ):
            print(event)
