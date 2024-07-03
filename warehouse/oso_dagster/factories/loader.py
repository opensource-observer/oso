from typing import List, Dict, Any
from types import ModuleType
import importlib
import pkgutil

from dagster import (
    SensorDefinition,
    JobDefinition,
    AssetChecksDefinition,
    load_assets_from_modules,
)

from .common import AssetFactoryResponse, AssetList, EarlyResourcesAssetFactory


def load_all_assets_from_package(
    package: ModuleType, early_resources: Dict[str, Any]
) -> AssetFactoryResponse:
    """Loads all assets and factories from a given package and any submodules it may have"""
    package_path = package.__path__

    modules: List[ModuleType] = []

    for module_info in pkgutil.walk_packages(package_path, package.__name__ + "."):
        module_name = module_info.name
        module = importlib.import_module(module_name)
        modules.append(module)
    factories = load_assets_factories_from_modules(modules, early_resources)
    asset_defs = load_assets_from_modules(modules)
    factory_assets = list(factories.assets)
    factory_assets.extend(asset_defs)
    return AssetFactoryResponse(
        assets=factory_assets,
        sensors=factories.sensors,
        jobs=factories.jobs,
        checks=factories.checks,
    )


def load_assets_factories_from_modules(
    modules: List[ModuleType],
    early_resources: Dict[str, Any],
) -> AssetFactoryResponse:
    assets: AssetList = []
    sensors: List[SensorDefinition] = []
    jobs: List[JobDefinition] = []
    checks: List[AssetChecksDefinition] = []
    for module in modules:
        for _, obj in module.__dict__.items():
            if isinstance(obj, EarlyResourcesAssetFactory):
                resp = obj(**early_resources)
                assets.extend(resp.assets)
                sensors.extend(resp.sensors)
                jobs.extend(resp.jobs)
                checks.extend(resp.checks)
            elif isinstance(obj, AssetFactoryResponse):
                assets.extend(obj.assets)
                sensors.extend(obj.sensors)
                jobs.extend(obj.jobs)
                checks.extend(obj.checks)
    return AssetFactoryResponse(
        assets=assets, sensors=sensors, jobs=jobs, checks=checks
    )
