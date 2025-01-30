import logging
import typing as t
from datetime import datetime, timedelta

from metrics_tools.local.config import (
    Config,
    DestinationLoader,
    TableMappingDestination,
)

logger = logging.getLogger(__name__)


class LocalWarehouseManager:
    @classmethod
    def from_config(
        cls,
        config: Config,
    ):
        return cls(config)

    def __init__(
        self,
        config: Config,
    ):
        self.config = config
        self.table_mapping = config.table_mapping

    def load_tables_into(self, loader: DestinationLoader):
        start = datetime.now() - timedelta(days=self.config.max_days)
        end = datetime.now()
        for source_name, destination in self.table_mapping.items():
            if isinstance(destination, str):
                destination = TableMappingDestination(table=destination)
            loader.load_from_bq(start, end, source_name, destination)
        logger.info("Loaded all tables into warehouse")

    def initialize(self):
        """Initializes the sqlmesh warehouse with the necessary source tables."""

        with self.config.loader_instance() as loader:
            self.load_tables_into(loader)
        logger.info("Completed local initialization")

    def reset(self, full_reset: bool = False):
        """Resets the sqlmesh warehouse to a clean state. If full_reset is True,
        all of the source data is also dropped and all data is reinitialized."""

        with self.config.loader_instance() as loader:
            if full_reset:
                loader.drop_all()
                self.load_tables_into(loader)
            else:
                loader.drop_non_sources()

    def sqlmesh(self, extra_args: t.List[str] = [], extra_env: t.Dict[str, str] = {}):
        """Runs the sqlmesh pipeline to materialize the warehouse."""
        with self.config.loader_instance() as loader:
            loader.sqlmesh(extra_args=extra_args, extra_env=extra_env)
