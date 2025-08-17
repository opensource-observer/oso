import typing as t

import structlog
from dagster import AssetKey, AssetsDefinition, ResourceParam
from dagster_sqlmesh import DagsterSQLMeshController, SQLMeshContextConfig
from dagster_sqlmesh.controller.base import DEFAULT_CONTEXT_FACTORY
from oso_core.cache.types import CacheMetadataOptions
from oso_dagster.config import DagsterConfig
from oso_dagster.factories.common import CacheableDagsterContext
from oso_dagster.resources.sqlmesh import SQLMeshExportedAssetDefinition
from pydantic import BaseModel
from sqlmesh.core.model import Model

from ..factories import AssetFactoryResponse, cacheable_asset_factory
from ..resources import PrefixedSQLMeshTranslator, SQLMeshExporter

logger = structlog.get_logger(__name__)


class SQLMeshExportedAssetsCollection(BaseModel):
    """A collection of SQLMesh exported assets."""

    assets_map: dict[str, SQLMeshExportedAssetDefinition]


@cacheable_asset_factory(tags=dict(run_at_build="true"))
def sqlmesh_export_factory(
    global_config: DagsterConfig,
    cache_context: CacheableDagsterContext,
):
    @cache_context.register_generator(
        cacheable_type=SQLMeshExportedAssetsCollection,
        extra_cache_key_metadata=dict(
            sqlmesh_gateway=global_config.sqlmesh_gateway,
        ),
        cache_metadata_options=CacheMetadataOptions.with_no_expiration_if(
            global_config.run_mode == "build" and global_config.in_deployed_container
        ),
    )
    def cacheable_exported_assets_defs(
        sqlmesh_infra_config: dict,
        sqlmesh_context_config: SQLMeshContextConfig,
        sqlmesh_translator: PrefixedSQLMeshTranslator,
        sqlmesh_exporters: ResourceParam[t.List[SQLMeshExporter]],
    ) -> SQLMeshExportedAssetsCollection:
        environment = sqlmesh_infra_config["environment"]

        controller = DagsterSQLMeshController.setup_with_config(
            config=sqlmesh_context_config,
            context_factory=DEFAULT_CONTEXT_FACTORY,
        )
        assets_map: dict[str, SQLMeshExportedAssetDefinition] = {}

        with controller.instance(environment) as mesh:
            models = mesh.models()
            models_to_export: t.List[t.Tuple[Model, AssetKey]] = []
            for name, model in models.items():
                if "export" not in model.tags:
                    continue
                models_to_export.append(
                    (
                        model,
                        sqlmesh_translator.get_asset_key(mesh.context, model.fqn),
                    )
                )

            # Create a export assets for this
            for exporter in sqlmesh_exporters:
                asset_def = exporter.create_export_asset(
                    mesh,
                    sqlmesh_translator,
                    to_export=models_to_export,
                )
                assets_map[exporter.name()] = asset_def

        return SQLMeshExportedAssetsCollection(assets_map=assets_map)

    @cache_context.register_hydrator()
    def hydrate_exported_assets_defs(
        cacheable_exported_assets_defs: SQLMeshExportedAssetsCollection,
        sqlmesh_exporters: ResourceParam[t.List[SQLMeshExporter]],
    ) -> AssetFactoryResponse:
        """hydrate the exported assets definitions."""
        hydrated_assets: list[AssetsDefinition] = []
        for exporter in sqlmesh_exporters:
            if exporter.name() in cacheable_exported_assets_defs.assets_map:
                asset_def = cacheable_exported_assets_defs.assets_map[exporter.name()]
                hydrated_assets.append(exporter.asset_from_definition(asset_def))
            else:
                logger.warning(
                    "Exporter not found in cached assets",
                    exporter_name=exporter.name(),
                )

        return AssetFactoryResponse(
            assets=hydrated_assets,
        )

    return cache_context
