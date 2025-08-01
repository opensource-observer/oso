import typing as t
from pathlib import Path
from traceback import print_exception

import structlog
from dagster import AssetKey, AssetsDefinition, ResourceParam
from dagster_sqlmesh import (
    DagsterSQLMeshCacheOptions,
    DagsterSQLMeshController,
    SQLMeshContextConfig,
)
from dagster_sqlmesh.controller.base import DEFAULT_CONTEXT_FACTORY
from oso_dagster.resources.sqlmesh import SQLMeshExportedAssetDefinition
from sqlmesh.core.model import Model

from ..factories import AssetFactoryResponse, early_resources_asset_factory
from ..resources import PrefixedSQLMeshTranslator, SQLMeshExporter

logger = structlog.get_logger(__name__)


@early_resources_asset_factory()
def sqlmesh_export_factory(
    sqlmesh_infra_config: dict,
    sqlmesh_context_config: SQLMeshContextConfig,
    sqlmesh_translator: PrefixedSQLMeshTranslator,
    sqlmesh_exporters: ResourceParam[t.List[SQLMeshExporter]],
    sqlmesh_cache_options: DagsterSQLMeshCacheOptions,
):
    environment = sqlmesh_infra_config["environment"]

    controller = DagsterSQLMeshController.setup_with_config(
        config=sqlmesh_context_config,
        context_factory=DEFAULT_CONTEXT_FACTORY,
    )
    assets: list[AssetsDefinition] = []

    missing_exporters = set()

    # Hack for now to cache all of the sqlmesh export assets
    if sqlmesh_cache_options.enabled:
        logger.info("SQLMesh export cache is enabled, caching assets")

        cache_dir = Path(sqlmesh_cache_options.cache_dir)
        exporter_assets_cache_dir = cache_dir.joinpath("sqlmesh_export_assets")
        # Ensure the cache directory exists
        exporter_assets_cache_dir.mkdir(parents=True, exist_ok=True)

        for exporter in sqlmesh_exporters:
            # Load the definition from the exporter
            cache_file = exporter_assets_cache_dir / f"{exporter.name()}.json"
            if cache_file.exists():
                logger.debug(f"Loading cached asset definition for {exporter.name()}")
                exporter_asset_def = SQLMeshExportedAssetDefinition.model_validate_json(
                    cache_file.read_text()
                )
                assets.append(exporter.asset_from_definition(exporter_asset_def))
            else:
                missing_exporters.add(exporter.name())
    else:
        missing_exporters = set(exporter.name() for exporter in sqlmesh_exporters)

    if len(missing_exporters) > 0:
        try:
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
                    if sqlmesh_cache_options.enabled:
                        cache_dir = Path(sqlmesh_cache_options.cache_dir)
                        exporter_assets_cache_dir = cache_dir.joinpath(
                            "sqlmesh_export_assets"
                        )

                        # Save the asset definition to the cache
                        cache_file = (
                            exporter_assets_cache_dir / f"{exporter.name()}.json"
                        )
                        logger.debug(
                            f"Caching asset definition for {exporter.name()} at {cache_file}"
                        )
                        cache_file.write_text(asset_def.model_dump_json())

                    assets.append(exporter.asset_from_definition(asset_def))
                    logger.debug(f"exporting for {exporter.name()}")
        except Exception as e:
            logger.exception(
                "Failed to create SQLMesh export assets",
                error=str(e),
            )
            print_exception(e)
            raise e

    return AssetFactoryResponse(assets=assets)
