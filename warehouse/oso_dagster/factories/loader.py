import importlib
import pkgutil
import typing as t
from graphlib import TopologicalSorter
from types import ModuleType

from dagster import load_assets_from_modules

from .common import AssetFactoryResponse, EarlyResourcesAssetFactory


class EarlyResourcesAssetFactoryDAG:
    def __init__(self):
        self._graph: t.Dict[
            EarlyResourcesAssetFactory, t.Set[EarlyResourcesAssetFactory]
        ] = {}
        self._sorted: (
            t.List[
                t.Tuple[EarlyResourcesAssetFactory, t.Set[EarlyResourcesAssetFactory]]
            ]
            | None
        ) = None

    def add(self, resource_factory: EarlyResourcesAssetFactory):
        self._graph[resource_factory] = set(resource_factory.dependencies)
        self._sorted = None

    def sorted(self):
        if not self._sorted:
            sorter = TopologicalSorter(self._graph)
            sorted = sorter.static_order()
            self._sorted = []
            for factory in sorted:
                self._sorted.append((factory, self._graph[factory]))

        return self._sorted


def load_all_assets_from_package(
    package: ModuleType, early_resources: t.Dict[str, t.Any]
) -> AssetFactoryResponse:
    """Loads all assets and factories from a given package and any submodules it may have"""
    package_path = package.__path__

    modules: t.List[ModuleType] = []
    early_resources_dag: EarlyResourcesAssetFactoryDAG = EarlyResourcesAssetFactoryDAG()

    for module_info in pkgutil.walk_packages(package_path, package.__name__ + "."):
        module_name = module_info.name
        module = importlib.import_module(module_name)
        modules.append(module)
    factories = load_assets_factories_from_modules(modules, early_resources_dag)

    resolved_factories: t.Dict[EarlyResourcesAssetFactory, AssetFactoryResponse] = {}

    # Resolve all early factories in topological order
    for early_factory, deps in early_resources_dag.sorted():
        resolved_deps = [resolved_factories[factory] for factory in deps]

        resp = early_factory(dependencies=resolved_deps, **early_resources)

        resolved_factories[early_factory] = resp
        factories = factories + resp

    asset_defs = load_assets_from_modules(modules)
    return factories + AssetFactoryResponse(asset_defs)


def load_assets_factories_from_modules(
    modules: t.List[ModuleType],
    dag: EarlyResourcesAssetFactoryDAG,
) -> AssetFactoryResponse:
    all = AssetFactoryResponse([])
    for module in modules:
        module_dict = module.__dict__.copy()
        for _, obj in module_dict.items():
            if isinstance(obj, EarlyResourcesAssetFactory):
                # resp = obj(**early_resources)
                # all = all + resp
                dag.add(obj)
            elif isinstance(obj, AssetFactoryResponse):
                all = all + obj
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, EarlyResourcesAssetFactory):
                        dag.add(item)
                    elif isinstance(item, AssetFactoryResponse):
                        all = all + item
    return all
