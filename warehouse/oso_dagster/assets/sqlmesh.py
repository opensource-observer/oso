from dagster import AssetExecutionContext, AssetKey
from dagster_sqlmesh import (
    SQLMeshContextConfig,
    SQLMeshDagsterTranslator,
    SQLMeshResource,
    sqlmesh_assets,
)
from oso_dagster.utils.asynctools import safe_async_run
from oso_dagster.utils.http import wait_for_ok
from oso_dagster.utils.kube.scaler import ensure_scale_down, ensure_scale_up
from sqlmesh import Context
from sqlmesh.core.model import Model

from ..factories import early_resources_asset_factory


class PrefixedSQLMeshTranslator(SQLMeshDagsterTranslator):
    def __init__(self, prefix: str):
        self._prefix = prefix

    def get_asset_key_fqn(self, context: Context, fqn: str) -> AssetKey:
        key = super().get_asset_key_fqn(context, fqn)
        return key.with_prefix("production").with_prefix("dbt")

    def get_asset_key_from_model(self, context: Context, model: Model) -> AssetKey:
        key = super().get_asset_key_from_model(context, model)
        return key.with_prefix(self._prefix)


@early_resources_asset_factory()
def sqlmesh_factory(sqlmesh_infra_config: dict, sqlmesh_config: SQLMeshContextConfig):
    environment = sqlmesh_infra_config["environment"]
    mcs_deployment_name = sqlmesh_infra_config["mcs_deployment_name"]
    mcs_deployment_namespace = sqlmesh_infra_config["mcs_deployment_namespace"]
    trino_deployment_namespace = sqlmesh_infra_config["trino_deployment_namespace"]
    trino_coordinator_deployment_name = sqlmesh_infra_config[
        "trino_coordinator_deployment_name"
    ]
    trino_worker_deployment_name = sqlmesh_infra_config["trino_worker_deployment_name"]

    @sqlmesh_assets(
        config=sqlmesh_config,
        environment=environment,
        dagster_sqlmesh_translator=PrefixedSQLMeshTranslator("metrics"),
    )
    def sqlmesh_project(context: AssetExecutionContext, sqlmesh: SQLMeshResource):
        context.log.info("Ensuring the mcs has scaled up")
        safe_async_run(
            ensure_scale_up(
                name=mcs_deployment_name, namespace=mcs_deployment_namespace, scale=1
            )
        )
        context.log.info("Ensure the trino coordinator has scaled up")
        safe_async_run(
            ensure_scale_up(
                name=trino_coordinator_deployment_name,
                namespace=trino_deployment_namespace,
                scale=1,
            )
        )
        context.log.info("Ensure the trino worker has scaled up")
        safe_async_run(
            ensure_scale_up(
                name=trino_worker_deployment_name,
                namespace=trino_deployment_namespace,
                scale=1,
            )
        )

        context.log.info("Waiting for the mcs to come online")
        wait_for_ok(
            f"http://{mcs_deployment_name}.{mcs_deployment_namespace}.svc.cluster.local:8000/status"
        )

        context.log.info("Waiting for the trino coordinator to come online")
        wait_for_ok(
            f"http://{trino_coordinator_deployment_name}.{trino_deployment_namespace}.svc.cluster.local:8080/"
        )

        yield from sqlmesh.run(context, environment=environment)

        safe_async_run(
            ensure_scale_down(
                name=trino_coordinator_deployment_name,
                namespace=trino_deployment_namespace,
            )
        )

        safe_async_run(
            ensure_scale_down(
                name=trino_worker_deployment_name,
                namespace=trino_deployment_namespace,
            )
        )

        safe_async_run(
            ensure_scale_down(
                name=mcs_deployment_name,
                namespace=mcs_deployment_namespace,
            )
        )

    return sqlmesh_project
