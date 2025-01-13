import logging
import typing as t

from dagster import AssetKey, ResourceParam
from dagster_sqlmesh import (
    DagsterSQLMeshController,
    SQLMeshContextConfig,
    SQLMeshDagsterTranslator,
)
from sqlmesh.core.model import Model

from ..factories import AssetFactoryResponse, early_resources_asset_factory
from ..resources import SQLMeshExporter

logger = logging.getLogger(__name__)


@early_resources_asset_factory()
def sqlmesh_export_factory(
    sqlmesh_infra_config: dict,
    sqlmesh_config: SQLMeshContextConfig,
    sqlmesh_translator: SQLMeshDagsterTranslator,
    sqlmesh_exporters: ResourceParam[t.List[SQLMeshExporter]],
):
    environment = sqlmesh_infra_config["environment"]

    controller = DagsterSQLMeshController.setup_with_config(sqlmesh_config)
    assets = []

    with controller.instance(environment) as mesh:
        models = mesh.models()
        models_to_export: t.List[t.Tuple[Model, AssetKey]] = []
        for name, model in models.items():
            if "export" not in model.tags:
                continue
            models_to_export.append(
                (
                    model,
                    sqlmesh_translator.get_asset_key_from_model(mesh.context, model),
                )
            )

        # Create a export assets for this
        for exporter in sqlmesh_exporters:
            asset_def = exporter.create_export_asset(
                mesh,
                to_export=models_to_export,
            )
            assets.append(asset_def)
            logger.debug(f"exporting for {exporter.__class__.__name__}")

    return AssetFactoryResponse(assets=assets)