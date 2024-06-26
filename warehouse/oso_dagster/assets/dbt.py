from pathlib import Path
import os
from typing import Any, Mapping, Dict, List, Sequence, Optional

from dagster import AssetExecutionContext, AssetKey, AssetsDefinition, Config
from dagster_dbt import DbtCliResource, dbt_assets, DagsterDbtTranslator

from ..constants import main_dbt_manifests, main_dbt_project_dir, dbt_profiles_dir


class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    def __init__(
        self,
        prefix: Sequence[str],
        internal_schema_map: Dict[str, List[str]],
    ):
        self._prefix = prefix
        self._internal_schema_map = internal_schema_map

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


class DBTConfig(Config):
    full_refresh: bool = False


def generate_dbt_asset(
    project_dir: Path | str,
    dbt_profiles_dir: Path | str,
    target: str,
    manifest_path: Path | str,
    internal_map: Dict[str, List[str]],
):
    print(f"Target[{target}] using profiles dir {dbt_profiles_dir}")
    translator = CustomDagsterDbtTranslator(["dbt", target], internal_map)

    @dbt_assets(
        name=f"{target}_dbt",
        manifest=manifest_path,
        dagster_dbt_translator=translator,
    )
    def _generated_dbt_assets(context: AssetExecutionContext, config: DBTConfig):
        print(f"using profiles dir {dbt_profiles_dir}")
        dbt = DbtCliResource(
            project_dir=os.fspath(project_dir),
            target=target,
            profiles_dir=f"{dbt_profiles_dir}",
        )
        build_args = ["build"]
        if config.full_refresh:
            build_args += ["--full-refresh"]
        yield from dbt.cli(build_args, context=context).stream()

    return _generated_dbt_assets


def dbt_assets_from_manifests_map(
    project_dir: Path | str,
    manifests: Dict[str, Path],
    internal_map: Optional[Dict[str, List[str]]] = None,
) -> List[AssetsDefinition]:
    if not internal_map:
        internal_map = {}
    assets: List[AssetsDefinition] = []
    for target, manifest_path in manifests.items():
        assets.append(
            generate_dbt_asset(
                project_dir, dbt_profiles_dir, target, manifest_path, internal_map
            )
        )

    return assets


all_dbt_assets = dbt_assets_from_manifests_map(
    main_dbt_project_dir,
    main_dbt_manifests,
    {
        "oso": ["dbt", "production"],
        "oso_base_playground": ["dbt", "base_playground"],
        "oso_playground": ["dbt", "playground"],
    },
)
