import typing as t
from typing import Any, List, Optional, Union

from scheduler.graphql_client.base_model import UNSET, UnsetType
from scheduler.graphql_client.create_materialization import CreateMaterialization
from scheduler.graphql_client.enums import RunStatus, StepStatus
from scheduler.graphql_client.finish_run import FinishRun
from scheduler.graphql_client.finish_step import FinishStep
from scheduler.graphql_client.get_data_ingestion_config import GetDataIngestionConfig
from scheduler.graphql_client.get_data_models import GetDataModels
from scheduler.graphql_client.get_run import GetRun
from scheduler.graphql_client.get_static_models import GetStaticModels
from scheduler.graphql_client.input_types import (
    DataModelColumnInput,
    UpdateMetadataInput,
)
from scheduler.graphql_client.resolve_tables import ResolveTables
from scheduler.graphql_client.start_run import StartRun
from scheduler.graphql_client.start_step import StartStep
from scheduler.graphql_client.update_run_metadata import UpdateRunMetadata


class ClientProtocol(t.Protocol):
    async def start_run(self, run_id: str, **kwargs: Any) -> StartRun: ...

    async def update_run_metadata(
        self, run_id: str, metadata: UpdateMetadataInput, **kwargs: Any
    ) -> UpdateRunMetadata: ...

    async def finish_run(
        self,
        run_id: str,
        status: RunStatus,
        status_code: int,
        logs_url: str,
        metadata: Union[Optional[UpdateMetadataInput], UnsetType] = UNSET,
        **kwargs: Any,
    ) -> FinishRun: ...

    async def start_step(
        self, run_id: str, name: str, display_name: str, **kwargs: Any
    ) -> StartStep: ...

    async def finish_step(
        self, step_id: str, status: StepStatus, logs_url: str, **kwargs: Any
    ) -> FinishStep: ...

    async def create_materialization(
        self,
        step_id: str,
        table_id: str,
        warehouse_fqn: str,
        schema: List[DataModelColumnInput],
        **kwargs: Any,
    ) -> CreateMaterialization: ...

    async def get_run(self, run_id: str, **kwargs: Any) -> GetRun: ...

    async def get_data_models(
        self, dataset_id: str, **kwargs: Any
    ) -> GetDataModels: ...

    async def get_data_ingestion_config(
        self, dataset_id: str, **kwargs: Any
    ) -> GetDataIngestionConfig: ...

    async def get_static_models(
        self, dataset_id: str, **kwargs: Any
    ) -> GetStaticModels: ...

    async def resolve_tables(
        self,
        references: List[str],
        metadata: Union[Optional[Any], UnsetType] = UNSET,
        **kwargs: Any,
    ) -> ResolveTables: ...

    def boop(self) -> int: ...
