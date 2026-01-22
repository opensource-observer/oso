from typing import Any, List, Optional, Union

from polyfactory.factories.pydantic_factory import ModelFactory
from scheduler.graphql_client.base_model import UNSET, UnsetType
from scheduler.graphql_client.create_materialization import CreateMaterialization
from scheduler.graphql_client.enums import RunStatus, StepStatus
from scheduler.graphql_client.finish_run import FinishRun
from scheduler.graphql_client.finish_step import FinishStep
from scheduler.graphql_client.get_data_ingestion_config import GetDataIngestionConfig
from scheduler.graphql_client.get_data_models import GetDataModels
from scheduler.graphql_client.get_notebook import GetNotebook
from scheduler.graphql_client.get_run import GetRun
from scheduler.graphql_client.get_static_models import GetStaticModels
from scheduler.graphql_client.input_types import (
    DataModelColumnInput,
    UpdateMetadataInput,
)
from scheduler.graphql_client.protocol import ClientProtocol
from scheduler.graphql_client.resolve_tables import ResolveTables
from scheduler.graphql_client.save_published_notebook_html import (
    SavePublishedNotebookHtml,
)
from scheduler.graphql_client.start_run import StartRun
from scheduler.graphql_client.start_step import StartStep
from scheduler.graphql_client.update_run_metadata import UpdateRunMetadata


class FakeClientProtocol(ClientProtocol):
    async def start_run(self, run_id: str, **kwargs: Any) -> StartRun:
        return ModelFactory.create_factory(StartRun).build()

    async def update_run_metadata(
        self, run_id: str, metadata: UpdateMetadataInput, **kwargs: Any
    ) -> UpdateRunMetadata:
        return ModelFactory.create_factory(UpdateRunMetadata).build()

    async def finish_run(
        self,
        run_id: str,
        status: RunStatus,
        status_code: int,
        logs_url: str,
        metadata: Union[Optional[UpdateMetadataInput], UnsetType] = UNSET,
        **kwargs: Any,
    ) -> FinishRun:
        return ModelFactory.create_factory(FinishRun).build()

    async def start_step(
        self, run_id: str, name: str, display_name: str, **kwargs: Any
    ) -> StartStep:
        return ModelFactory.create_factory(StartStep).build()

    async def finish_step(
        self, step_id: str, status: StepStatus, logs_url: str, **kwargs: Any
    ) -> FinishStep:
        return ModelFactory.create_factory(FinishStep).build()

    async def create_materialization(
        self,
        step_id: str,
        table_id: str,
        warehouse_fqn: str,
        schema: List[DataModelColumnInput],
        **kwargs: Any,
    ) -> CreateMaterialization:
        return ModelFactory.create_factory(CreateMaterialization).build()

    async def save_published_notebook_html(
        self, notebook_id: str, html_content: str, **kwargs: Any
    ) -> SavePublishedNotebookHtml:
        return ModelFactory.create_factory(SavePublishedNotebookHtml).build()

    async def get_run(self, run_id: str, **kwargs: Any) -> GetRun:
        return ModelFactory.create_factory(GetRun).build()

    async def get_data_models(self, dataset_id: str, **kwargs: Any) -> GetDataModels:
        return ModelFactory.create_factory(GetDataModels).build()

    async def get_data_ingestion_config(
        self, dataset_id: str, **kwargs: Any
    ) -> GetDataIngestionConfig:
        return ModelFactory.create_factory(GetDataIngestionConfig).build()

    async def get_static_models(
        self, dataset_id: str, **kwargs: Any
    ) -> GetStaticModels:
        return ModelFactory.create_factory(GetStaticModels).build()

    async def resolve_tables(
        self,
        references: List[str],
        metadata: Union[Optional[Any], UnsetType] = UNSET,
        **kwargs: Any,
    ) -> ResolveTables:
        return ModelFactory.create_factory(ResolveTables).build()

    async def get_notebook(self, notebook_id: str, **kwargs: Any) -> GetNotebook:
        return ModelFactory.create_factory(GetNotebook).build()
