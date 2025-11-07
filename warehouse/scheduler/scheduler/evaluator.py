from scheduler.types import UserDefinedModelClient
from sqlmesh import EngineAdapter


async def evaluate_all_models(
    udm_client: UserDefinedModelClient, adapter: EngineAdapter
) -> None:
    """Our first pass at a hacky model evaluator. This should be immediately
    replaced as this simply checks available models in our database.

    Many model configuration options are simply ignored this evaluator will
    check all model releases and all model runs in the last 48 hours.

    For any releases that do not have a successful run in that time period will
    be run as part of the evaluation. This is obviously not great, but is a
    starting point.

    """

    # Pull all "latest" model releases from the database
    # Pull all model runs from the database in the last 48 hours
    latest_models = await udm_client.all_models_missing_runs()

    known_dbs: set[str] = set()

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
