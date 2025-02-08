import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from dagster import AssetExecutionContext, AssetKey, Config, RunConfig, define_asset_job
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets
from oso_dagster.config import DagsterConfig

from ..factories import AssetFactoryResponse, early_resources_asset_factory

logger = logging.getLogger(__name__)


class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    def __init__(
        self,
        environment: str,
        prefix: Sequence[str],
        internal_schema_map: Dict[str, List[str]],
    ):
        self._prefix = prefix
        self._internal_schema_map = internal_schema_map
        self._environment = environment

    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        asset_key = super().get_asset_key(dbt_resource_props)
        final_key = asset_key.with_prefix(self._prefix)
        # This is a temporary hack to get ossd as a top level item in production
        if (
            dbt_resource_props.get("source_name", "") == "ossd"
            and dbt_resource_props["schema"] == "oso"
            and dbt_resource_props.get("identifier", "").endswith("_ossd")
        ):
            return asset_key
        if dbt_resource_props["resource_type"] == "source":
            schema = dbt_resource_props["schema"]
            if schema in self._internal_schema_map:
                new_key = self._internal_schema_map[schema][:]
                new_key.append(dbt_resource_props["identifier"])
                final_key = AssetKey(new_key)
            else:
                final_key = asset_key
        return final_key

    def get_tags(self, dbt_resource_props: Mapping[str, Any]) -> Mapping[str, str]:
        tags: Dict[str, str] = dict()
        materialization = dbt_resource_props.get("config", {}).get("materialized")
        if materialization:
            tags["dbt/materialized"] = materialization
            tags["opensource.observer/environment"] = self._environment
        return tags


class DBTConfig(Config):
    full_refresh: bool = False


def generate_dbt_asset(
    project_dir: Path | str,
    dbt_profiles_dir: Path | str,
    target: str,
    manifest_path: Path | str,
    internal_map: Dict[str, List[str]],
    op_tags: Optional[Mapping[str, Any]] = None,
):
    """Generates a single Dagster dbt asset

    Parameters
    ----------
    project_dir: Path | str
        Absolute path to the repo root
    dbt_profiles_dir: Path | str
        Path to the dbt profiles directory (e.g. `~/.dbt`)
    target: str
        dbt target (e.g. "production" or "playground")
    manifest_path: Path | str
        Path to the manifest.json for a dbt target
    internal_map: Dict[str, List[str]]
        Something related to `CustomDagsterDbtTranslator`

    Returns
    -------
    AssetsDefinition
        a single Dagster dbt asset
    """
    logger.debug(f"Target[{target}] using profiles_dir({dbt_profiles_dir})")
    logger.debug(f"\tmanifest_path({manifest_path})")
    translator = CustomDagsterDbtTranslator(target, ["dbt", target], internal_map)

    asset_name = f"{target}_dbt"

    @dbt_assets(
        name=asset_name,
        manifest=manifest_path,
        dagster_dbt_translator=translator,
        op_tags=op_tags,
    )
    def _generated_dbt_assets(context: AssetExecutionContext, config: DBTConfig):
        logger.debug(f"using profiles dir {dbt_profiles_dir}")
        dbt = DbtCliResource(
            project_dir=os.fspath(project_dir),
            target=target,
            profiles_dir=f"{dbt_profiles_dir}",
        )
        build_args = ["build"]
        if config.full_refresh:
            build_args += ["--full-refresh"]
        yield from dbt.cli(build_args, context=context).stream()

    run_dbt_assets_job = define_asset_job(
        name=f"{target}_dbt_run_job", selection=[_generated_dbt_assets]
    )

    run_dbt_assets_full_refresh_job = define_asset_job(
        name=f"{target}_dbt_full_refresh_job",
        selection=[_generated_dbt_assets],
        config=RunConfig(
            {
                asset_name: DBTConfig(full_refresh=True),
            }
        ),
    )

    return AssetFactoryResponse(
        assets=[_generated_dbt_assets],
        jobs=[run_dbt_assets_job, run_dbt_assets_full_refresh_job],
    )


def dbt_assets_from_manifests_map(
    global_config: DagsterConfig,
    internal_map: Optional[Dict[str, List[str]]] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
) -> AssetFactoryResponse:
    """Creates all Dagster dbt assets from a map of manifests

    Parameters
    ----------
    project_dir: Path | str
        Absolute path to the repo root
    manifests: Dict[str, Path]
        Result from `load_dbt_manifests()`
        dbt_target => manifest_path
    internal_map: Optional[Dict[str, List[str]]]
        Something related to `CustomDagsterDbtTranslator`

    Returns
    -------
    List[AssetsDefinition]
        a list of Dagster assets
    """

    if not internal_map:
        internal_map = {}
    assets: AssetFactoryResponse = AssetFactoryResponse(
        assets=[],
    )
    manifests = global_config.dbt_manifests
    for target, manifest_path in manifests.items():
        assets += generate_dbt_asset(
            global_config.main_dbt_project_dir,
            global_config.dbt_profiles_dir,
            target,
            manifest_path,
            internal_map,
            op_tags,
        )

    return assets


op_tags = {
    "dagster-k8s/config": {
        "pod_spec_config": {
            "node_selector": {"pool_type": "standard"},
            "tolerations": [
                {
                    "key": "pool_type",
                    "operator": "Equal",
                    "value": "standard",
                    "effect": "NoSchedule",
                }
            ],
        },
        "merge_behavior": "SHALLOW",
    }
}


@early_resources_asset_factory()
def all_dbt_assets(global_config: DagsterConfig) -> AssetFactoryResponse:
    return dbt_assets_from_manifests_map(
        global_config,
        {
            "oso": ["dbt", "production"],
            "oso_base_playground": ["dbt", "base_playground"],
            "oso_playground": ["dbt", "playground"],
        },
        # For now dbt should run on non-spot nodes because we sometimes need to do
        # full-refreshes which should not be killed randomly (or as randomly)
        op_tags=op_tags,
    )
