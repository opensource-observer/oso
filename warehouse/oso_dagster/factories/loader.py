import importlib
import pkgutil
import typing as t
from graphlib import TopologicalSorter
from types import ModuleType

import structlog
from dagster import load_assets_from_modules
from oso_core.logging.utils import time_context

from .common import AssetFactoryResponse, EarlyResourcesAssetFactory, ResourcesContext

logger = structlog.get_logger(__name__)


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
    package: ModuleType,
    resources: ResourcesContext,
) -> AssetFactoryResponse:
    """Loads all assets and factories from a given package and any submodules it may have

    Args:
        package (ModuleType): The package to load assets and factories from.
        resources (ResourcesContext): The resources context to use for loading
            asset factories.

    Returns:
        AssetFactoryResponse: A response containing all loaded assets and factories.
    """
    package_path = package.__path__

    modules: t.List[ModuleType] = []
    early_resources_dag: EarlyResourcesAssetFactoryDAG = EarlyResourcesAssetFactoryDAG()

    for module_info in pkgutil.walk_packages(package_path, package.__name__ + "."):
        module_name = module_info.name
        with time_context(logger, f"loading module {module_name}"):
            module = importlib.import_module(module_name)
            modules.append(module)
    factories = load_assets_factories_from_modules(modules, early_resources_dag)

    resolved_factories: t.Dict[EarlyResourcesAssetFactory, AssetFactoryResponse] = {}

    # Resolve all early factories in topological order
    for early_factory, deps in early_resources_dag.sorted():
        resolved_deps = [resolved_factories[factory] for factory in deps]

        with time_context(
            logger,
            f"generating assets for '{early_factory.name}'",
            loading_from_module=early_factory.module,
        ):
            resp = early_factory(resources, dependencies=resolved_deps)

        resolved_factories[early_factory] = resp
        factories = factories + resp

    asset_defs = load_assets_from_modules(modules)
    return factories + AssetFactoryResponse(asset_defs)


def load_assets_factories_from_modules(
    modules: t.List[ModuleType],
    dag: EarlyResourcesAssetFactoryDAG,
) -> AssetFactoryResponse:
    """Loads all AssetFactoryResponses or EarlyResourcesAssetFactory's into a
    DAG. This is mostly an internal function and isn't intended to be called
    directly outside of this module.

    Args:
        modules (List[ModuleType]): The modules to load assets and factories
        from.
        dag (EarlyResourcesAssetFactoryDAG): A DAG to track early
        resources asset factories.

    Returns:
        AssetFactoryResponse: A response containing all loaded assets and
        factories.
    """
    all = AssetFactoryResponse([])
    for module in modules:
        with time_context(logger, f"loading assets from {module.__name__}"):
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
