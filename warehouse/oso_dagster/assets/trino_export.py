import typing as t

from dagster import ResourceParam
from dagster_sqlmesh import (
    DagsterSQLMeshController,
    SQLMeshContextConfig,
    SQLMeshDagsterTranslator,
)

from ..factories import AssetFactoryResponse, early_resources_asset_factory
from ..resources import SQLMeshExporter


@early_resources_asset_factory()
def trino_export_factory(
    sqlmesh_infra_config: dict,
    sqlmesh_config: SQLMeshContextConfig,
    sqlmesh_translator: SQLMeshDagsterTranslator,
    trino_exporters: ResourceParam[t.List[SQLMeshExporter]],
):
    environment = sqlmesh_infra_config["environment"]

    controller = DagsterSQLMeshController.setup_with_config(sqlmesh_config)
    assets = []
    with controller.instance(environment) as mesh:
        models = mesh.models()
        for name, model in models.items():
            if "export" not in model.tags:
                continue

            # Create a export assets for this
            for exporter in trino_exporters:
                assets.append(
                    exporter.create_export_asset(
                        mesh,
                        name,
                        model,
                        sqlmesh_translator.get_asset_key_from_model(
                            mesh.context, model
                        ),
                    )
                )

    return AssetFactoryResponse(assets=assets)
