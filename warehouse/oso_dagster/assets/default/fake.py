from dagster import asset, job, op
from oso_dagster.config import DagsterConfig
from oso_dagster.factories import AssetFactoryResponse, early_resources_asset_factory


@early_resources_asset_factory()
def fake_early_resources_asset(global_config: DagsterConfig) -> AssetFactoryResponse:
    @asset(compute_kind="fake", tags={"opensource.observer/experimental": "true"})
    def fake_failing_asset() -> None:
        raise Exception("This fake asset only ever fails")

    @op(tags={"kind": "fake"})
    def fake_failing_op() -> None:
        raise Exception("This fake op only ever fails")

    @job()
    def fake_failing_job():
        fake_failing_op()

    if global_config.test_assets_enabled:
        return AssetFactoryResponse(
            assets=[fake_failing_asset], jobs=[fake_failing_job]
        )
    else:
        return AssetFactoryResponse(assets=[])
