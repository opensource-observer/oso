from typing import List, Dict, Any
from types import ModuleType
import importlib
import pkgutil

from dagster import (
    load_assets_from_modules,
)

from .common import AssetFactoryResponse, EarlyResourcesAssetFactory


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
    return factories + AssetFactoryResponse(asset_defs)


def load_assets_factories_from_modules(
    modules: List[ModuleType],
    early_resources: Dict[str, Any],
) -> AssetFactoryResponse:
    all = AssetFactoryResponse([])
    for module in modules:
        for _, obj in module.__dict__.items():
            if isinstance(obj, EarlyResourcesAssetFactory):
                resp = obj(**early_resources)
                all = all + resp
            elif isinstance(obj, AssetFactoryResponse):
                all = all + obj
    return all
