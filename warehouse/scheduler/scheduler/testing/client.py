import uuid

from scheduler.graphql_client import (
    CreateMaterialization,
    DataModelColumnInput,
    FinishRun,
    FinishStep,
    RunStatus,
    StartRun,
    StartStep,
    StepStatus,
)
from scheduler.graphql_client.client import Client as OSOClient
from scheduler.types import Model, UserDefinedModelStateClient


class FakeUDMClient(UserDefinedModelStateClient):
    def __init__(self):
        self._models: list[Model] = []
        super().__init__()

    async def all_models_missing_runs(self) -> list[Model]:
        return self._models

    def add_model(self, model: Model) -> None:
        self._models.append(model)


class FakeOSOClient(OSOClient):
    def __init__(self):
        pass  # No need to call super().__init__()

    async def create_materialization(
        self,
        step_id: str,
        table_id: str,
        warehouse_fqn: str,
        schema: list[DataModelColumnInput],
        **kwargs,
    ):
        return CreateMaterialization.model_validate(
            {
                "createMaterialization": {
                    "success": True,
                    "materialization": {"id": str(uuid.uuid4())},
                }
            }
        )

    async def start_run(self, run_id: str, **kwargs):
        return StartRun.model_validate(
            {
                "startRun": {
                    "success": True,
                }
            }
        )

    async def start_step(self, run_id: str, name: str, display_name: str, **kwargs):
        return StartStep.model_validate(
            {"startStep": {"success": True, "step": {"id": str(uuid.uuid4())}}}
        )

    async def finish_step(self, step_id: str, status: StepStatus, logs_url, **kwargs):
        return FinishStep.model_validate(
            {"finishStep": {"success": True, "message": "", "step": {"id": step_id}}}
        )

    async def finish_run(self, run_id: str, status: RunStatus, logs_url: str, **kwargs):
        return FinishRun.model_validate(
            {"finishRun": {"success": True, "message": "", "run": {"id": run_id}}}
        )
