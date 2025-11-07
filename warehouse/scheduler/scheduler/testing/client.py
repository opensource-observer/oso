from scheduler.types import Model, UserDefinedModelClient


class FakeUDMClient(UserDefinedModelClient):
    def __init__(self):
        self._models: list[Model] = []
        super().__init__()

    async def all_models_missing_runs(self) -> list[Model]:
        return self._models

    def add_model(self, model: Model) -> None:
        self._models.append(model)
