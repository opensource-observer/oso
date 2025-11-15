import typing as t

from scheduler.types import UserDefinedModelStateClient
from sqlmesh import EngineAdapter


class UserDefinedModelEvaluator:
    """Evaluates user defined models and runs them using the provided engine adapter."""

    @classmethod
    def prepare(cls, udm_client: UserDefinedModelStateClient):
        """Prepares the evaluator with the given UDM client."""

        return cls(udm_client)

    def __init__(self, udm_client: UserDefinedModelStateClient):
        self._udm_client = udm_client

    async def evaluate(
        self,
        adapter_context_manager: t.Callable[[], t.AsyncContextManager[EngineAdapter]],
    ) -> None:
        """Our first pass at a hacky model evaluator. This should be immediately
        replaced as this simply checks available models in our database.

        Many model configuration options are simply ignored this evaluator will
        check all model releases and all model runs in the last 48 hours.

        For any releases that do not have a successful run in that time period
        will be run as part of the evaluation. This is obviously not great, but
        is a starting point.

        Args:
            adapter_context_manager: A callable that returns an async context
                manager for the engine adapter to use when running models. We
                use a context manager here so we don't have to connect to the
                engine adapter until we know we have work to do.

        Returns:
            None
        """

        # Pull all "latest" model releases from the database
        # Pull all model runs from the database in the last 48 hours
        latest_models = await self._udm_client.all_models_missing_runs()

        known_dbs: set[str] = set()

        async with adapter_context_manager() as adapter:
            for model in latest_models:
                db_name = model.backend_db_name()
                if db_name in known_dbs:
                    continue
                adapter.create_schema(db_name, ignore_if_exists=True)
                known_dbs.add(db_name)

            for model in latest_models:
                # TODO we don't handle changes to model schema right now. We instead
                # stupidly attempt to run the model regardless of changes.
                adapter.ctas(
                    table_name=model.backend_table(),
                    query_or_df=model.ctas_query(),
                    exists=True,
                )

                adapter.insert_append(
                    table_name=model.backend_table(),
                    query_or_df=model.query,
                )
