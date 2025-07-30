import inspect
import logging
import typing as t
from dataclasses import dataclass, field
from graphlib import TopologicalSorter

from dagster import (
    AssetChecksDefinition,
    AssetsDefinition,
    AssetSpec,
    JobDefinition,
    SensorDefinition,
    SourceAsset,
)
from oso_dagster.config import DagsterConfig
from oso_dagster.utils import dagsterinternals as dginternals

type GenericAsset = t.Union[
    AssetsDefinition, SourceAsset, dginternals.CacheableAssetsDefinition, AssetSpec
]
type NonCacheableAssetsDefinition = t.Union[AssetsDefinition, SourceAsset]
type AssetList = t.Iterable[GenericAsset]
type AssetDeps = t.Iterable[dginternals.CoercibleToAssetDep]
type AssetKeyPrefixParam = dginternals.CoercibleToAssetKeyPrefix
type FactoryJobDefinition = JobDefinition | dginternals.UnresolvedAssetJobDefinition

logger = logging.getLogger(__name__)


class GenericGCSAsset:
    def clean_up(self):
        raise NotImplementedError()

    def sync(self):
        raise NotImplementedError()


@dataclass
class AssetFactoryResponse:
    assets: AssetList
    sensors: t.List[SensorDefinition] = field(default_factory=lambda: [])
    jobs: t.List[FactoryJobDefinition] = field(default_factory=lambda: [])
    checks: t.List[AssetChecksDefinition] = field(default_factory=lambda: [])

    def __add__(self, other: "AssetFactoryResponse") -> "AssetFactoryResponse":
        return AssetFactoryResponse(
            assets=list(self.assets) + list(other.assets),
            sensors=list(self.sensors) + list(other.sensors),
            checks=list(self.checks) + list(other.checks),
            jobs=list(self.jobs) + list(other.jobs),
        )

    def filter_assets(
        self, f: t.Callable[[NonCacheableAssetsDefinition], bool]
    ) -> t.Iterable[NonCacheableAssetsDefinition]:
        """Due to limitations of docs on CacheableAssetsDefinitions, we filter
        out any CacheableAssetsDefinitions as they cannot be compared against
        for filtering"""
        no_cacheable_assets = t.cast(
            t.List[NonCacheableAssetsDefinition],
            filter(
                lambda a: not isinstance(a, dginternals.CacheableAssetsDefinition),
                self.assets,
            ),
        )
        return filter(f, no_cacheable_assets)

    def filter_assets_by_name(self, name: str):
        """The asset "name" in this context is the final part of the asset key."""
        filtered = self.filter_assets(lambda a: a.key.path[-1] == name)
        return filtered

    def find_job_by_name(
        self, name: str
    ) -> t.Optional[t.Union[JobDefinition, dginternals.UnresolvedAssetJobDefinition]]:
        return next((job for job in self.jobs if job.name == name), None)


type EarlyResourcesAssetDecoratedFunction[**P] = t.Callable[
    P, AssetFactoryResponse | AssetsDefinition
]


@dataclass(kw_only=True)
class ResourceFactory:
    """A factory that is used to create resources for asset factories.
    This is used to inject resources into asset factories that require them."""

    name: str
    factory: t.Callable[..., t.Any]
    dependencies: t.Dict[str, t.Type]
    return_type: t.Type

    def __call__(self, **kwargs) -> t.Any:
        """Call the factory with the given arguments and return the resource."""
        return self.factory(**kwargs)


class ResourcesRegistry:
    """Out of the box, dagster doesn't have a concept of factories.
    Additionally, it doesn't have a concept of early resources. This class is a
    dependency injection registry that allows us to define factory functions
    for resources required by assets that use the EarlyResourcesAssetFactory. To
    improve performance, the factory functions used to create the resources
    should be fully self contained and declare all their imports in the function
    itself as opposed to at the module level. This allows us to avoid importing
    unnecessary modules when the resources are not used.
    """

    def __init__(
        self,
        resources: t.Optional[t.Dict[str, ResourceFactory]] = None,
        resources_dag: t.Optional[t.Dict[str, t.Set[str]]] = None,
    ):
        self._resources: t.Dict[str, ResourceFactory] = resources or {}
        self._resources_dag: t.Dict[str, t.Set[str]] = resources_dag or {}

    def clone(self) -> "ResourcesRegistry":
        """Clone the current resources registry. This is useful for creating a
        new registry with the same resources but without modifying the original
        one."""
        return ResourcesRegistry(
            resources=self._resources.copy(),
            resources_dag=self._resources_dag.copy(),
        )

    def add(self, resource_factory: ResourceFactory):
        """Add a resource factory to the early resources container."""
        if resource_factory.name == "resources":
            raise ValueError(
                "Resource factory with name 'resources' is reserved and cannot be used."
            )

        if resource_factory.name in self._resources:
            raise ValueError(
                f"Resource factory with name {resource_factory.name} already exists."
            )
        self._resources[resource_factory.name] = resource_factory
        self._resources_dag[resource_factory.name] = set(
            resource_factory.dependencies.keys()
        )

    def get(self, name: str) -> ResourceFactory:
        """Get a resource by name.

        If there are any dependencies for this resource, they will be
        automatically resolved and passed to the factory function. We do this in
        a very lazy way so that we only resolve the dependencies when the
        resource is actually needed.
        """

        if name not in self._resources:
            raise ValueError(f"Resource factory with name {name} does not exist.")
        return self._resources[name]

    def context(self) -> "ResourcesContext":
        """Create a context for the resources registry. This context is used to
        resolve resources and cache them for later use."""

        # Check the registry's dag to see if there are any cycles or missing dependencies.
        sorter = TopologicalSorter(self._resources_dag)
        sorter.prepare()

        # Create a clone of the registry to avoid any issues with new resources
        # being added
        return ResourcesContext(self.clone())


class ResourcesContext:
    """This is a dependency injection container that stores resolved resources.

    This dependency injection container only allows us to resolve resources
    once. So all resolved resources are cached and reused on subsequent
    requests.
    """

    def __init__(self, registry: ResourcesRegistry):
        self._registry = registry
        self._resolved_resources: t.Dict[str, t.Any] = {}

    def run[T](
        self,
        f: t.Callable[..., T],
        additional_annotations: t.Dict[str, t.Type] | None = None,
        additional_inject: t.Dict[str, t.Any] | None = None,
        **kwargs,
    ) -> T:
        """Run a function and resolve all the resources this function requires.

        Args:
            f (Callable[..., T]): The function to run.
            additional_annotations (Dict[str, Type], optional): Additional annotations
                to use for the function. This is useful for functions that require
                additional resources that are not defined in the function's
                annotations (for some reason).
            additional_inject (Dict[str, Any], optional): Additional resources to inject
                into the function. This is useful to override any injection or other
                defined annotations, this is different than kwargs because it
                isn't passed to the function unless the function explicitly
                requests it.
            **kwargs: Additional keyword arguments to pass to the function
                The values in kwargs are not modified in any way

        Returns:
            T: The result of the function.

        """
        additional_annotations = additional_annotations or {}
        additional_inject = additional_inject or {}
        annotations = f.__annotations__.copy()
        annotations.update(additional_annotations)

        resolved_resources: t.Dict[str, t.Any] = {}
        if "resources" in annotations:
            # If the function has a resources argument, we will pass the
            # ResourcesContext to it.
            resolved_resources["resources"] = self
        for key in annotations.keys():
            if key in ["return", "resources"]:
                continue
            if key in additional_inject:
                # If the key is in additional_inject, we will use that value.
                resolved_resources[key] = additional_inject[key]
                continue
            if key in kwargs:
                # If the key is already in kwargs, we don't need to resolve it.
                continue
            resolved_resources[key] = self.resolve(key)
        return f(**resolved_resources, **kwargs)

    def resolve(self, name: str) -> t.Any:
        """Resolve a resource by name. If the resource is not resolved yet, it
        will be resolved and cached."""

        if name not in self._resolved_resources:
            resource_factory = self._registry.get(name)

            deps: t.Dict[str, t.Any] = {}

            # Resolve all dependencies for the resource factory. We _shouldn't_ need to
            # worry about circular dependencies as we check for them at the time
            # of ResourceContext creation.
            for dep_name in resource_factory.dependencies.keys():
                deps[dep_name] = self.resolve(dep_name)

            self._resolved_resources[name] = resource_factory(**deps)
        return self._resolved_resources[name]


class EarlyResourcesAssetFactory:
    """Defines an asset factory that requires some resources upon starting. This
    is most useful for asset factories that require some form of secret and use
    the secret resolver."""

    def __init__(
        self,
        f: EarlyResourcesAssetDecoratedFunction,
        caller: t.Optional[inspect.FrameInfo] = None,
        additional_annotations: t.Optional[t.Dict[str, t.Any]] = None,
        dependencies: t.Optional[t.List["EarlyResourcesAssetFactory"]] = None,
    ):
        self._f = f
        self._caller = caller
        self.additional_annotations = additional_annotations or {}
        self._dependencies = dependencies or []

    def __call__(
        self, resources: ResourcesContext, dependencies: t.List[AssetFactoryResponse]
    ) -> AssetFactoryResponse:
        global_config = t.cast(DagsterConfig, resources.resolve("global_config"))
        assert global_config is not None, (
            "global_config is required for early resources"
        )
        try:
            res = resources.run(
                self._f,
                additional_annotations=self.additional_annotations,
                additional_inject=dict(dependencies=dependencies),
            )
        except Exception:
            if self._caller:
                logger.error(
                    f"Skipping failed asset factories from {self._caller.filename}",
                    exc_info=global_config.verbose_logs,
                )
            else:
                logger.error(
                    f"Skipping failed asset factories from {self._f.__module__}.{self._f.__name__}",
                    exc_info=global_config.verbose_logs,
                )
            return AssetFactoryResponse(assets=[])

        if isinstance(res, AssetFactoryResponse):
            return res
        elif isinstance(res, AssetsDefinition):
            return AssetFactoryResponse(assets=[res])
        else:
            raise Exception("Invalid early resource factory")

    @property
    def dependencies(self):
        return self._dependencies[:]


def early_resources_asset_factory(
    *,
    caller_depth: int = 1,
    additional_annotations: t.Optional[t.Dict[str, t.Any]] = None,
    dependencies: t.Optional[t.List[EarlyResourcesAssetFactory]] = None,
):
    caller = inspect.stack()[caller_depth]

    def _decorator(f: EarlyResourcesAssetDecoratedFunction):
        return EarlyResourcesAssetFactory(
            f,
            caller=caller,
            additional_annotations=additional_annotations,
            dependencies=dependencies,
        )

    return _decorator


def resource_factory(name: str):
    """A decorator that turns a normal function into a resource factory."""

    def _decorator(f: t.Callable[..., t.Any]) -> ResourceFactory:
        annotations = f.__annotations__
        return_type = annotations.get("return", t.Any)
        dependencies = {
            k: v for k, v in annotations.items() if k != "return" and v is not None
        }
        return ResourceFactory(
            name=name,
            factory=f,
            dependencies=dependencies,
            return_type=return_type,
        )

    return _decorator
