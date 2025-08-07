import inspect
import typing as t
from dataclasses import dataclass, field
from graphlib import TopologicalSorter

import structlog
from dagster import (
    AssetChecksDefinition,
    AssetsDefinition,
    AssetSpec,
    JobDefinition,
    SensorDefinition,
    SourceAsset,
)
from oso_core.cache import CacheBackend, CacheInvalidError
from oso_dagster.config import DagsterConfig
from oso_dagster.factories.cache import (
    CacheableAssetCheckOptions,
    CacheableAssetOptions,
    CacheableJobOptions,
    CacheableMultiAssetOptions,
    CacheableSensorOptions,
)
from oso_dagster.utils import dagsterinternals as dginternals
from pydantic import BaseModel

type GenericAsset = t.Union[
    AssetsDefinition, SourceAsset, dginternals.CacheableAssetsDefinition, AssetSpec
]
type NonCacheableAssetsDefinition = t.Union[AssetsDefinition, SourceAsset]
type AssetList = t.Iterable[GenericAsset]
type AssetDeps = t.Iterable[dginternals.CoercibleToAssetDep]
type AssetKeyPrefixParam = dginternals.CoercibleToAssetKeyPrefix
type FactoryJobDefinition = JobDefinition | dginternals.UnresolvedAssetJobDefinition

logger = structlog.get_logger(__name__)


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
    dependency injection registry that allows us to define factory functions for
    resources required by assets that use the EarlyResourcesAssetFactory. To
    improve performance, the factory functions used to create the resources
    should attempt to be self contained and declare most of their imports in the
    function itself as opposed to at the module level. Any imports done at the
    module level should be "pure" imports. By "pure", importing the module
    should have no side effects. Many of our assets are not structured this way,
    and so should be avoided in module level imports.
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

    # This is the reserved keyword used to reference the resources context in
    # function annotations that use the ResourcesContext + ResourcesRegistry
    resources_keyword_name = "resources"

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

        logger.debug(
            f"running function {f.__name__} with annotations",
            func_name=f.__name__,
            annotations=annotations,
        )

        resolved_resources: t.Dict[str, t.Any] = {}
        if ResourcesContext.resources_keyword_name in annotations:
            # If the function has a resources argument, we will pass the
            # ResourcesContext to it.
            resolved_resources[ResourcesContext.resources_keyword_name] = self
        for key in annotations.keys():
            if key in ["return", ResourcesContext.resources_keyword_name]:
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
    def name(self) -> str:
        """Get the name of the asset factory."""
        return self._f.__name__

    @property
    def caller_filename(self) -> str:
        if self._caller is None:
            return "<unknown>"
        return self._caller.filename

    @property
    def module(self) -> str:
        """Get the module of the asset factory."""
        return self._f.__module__

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


CacheableDagsterObjectGenerator = t.Callable[
    ...,
    t.Iterable[
        t.Union[
            CacheableAssetOptions,
            CacheableJobOptions,
            CacheableSensorOptions,
            CacheableAssetCheckOptions,
        ]
    ],
]


class CacheableContextEmitter(t.Protocol):
    """A protocol that defines the methods that a cache context emitter should implement."""

    def emit_job(self, handler_name: str, job_options: CacheableJobOptions):
        """Emit a job definition from the cacheable context."""
        ...

    def emit_sensor(self, handler_name: str, sensor_options: CacheableSensorOptions):
        """Emit a sensor definition from the cacheable context."""
        ...

    def emit_asset_check(
        self, handler_name: str, asset_check_options: CacheableAssetCheckOptions
    ):
        """Emit an asset check definition from the cacheable context."""
        ...

    def emit_asset(self, handler_name: str, asset_options: CacheableAssetOptions):
        """Emit an asset definition from the cacheable context."""
        ...

    def emit_multi_asset(
        self, handler_name: str, multi_asset_options: CacheableMultiAssetOptions
    ):
        """Emit a multi-asset definition from the cacheable context."""
        ...

    def add_generator(self, generator: CacheableDagsterObjectGenerator):
        """Add a generator to the cacheable context."""
        ...


class CacheableDagsterContextBindings(BaseModel):
    """A class that holds the bindings for a cacheable dagster context."""

    jobs: t.List[t.Tuple[str, CacheableJobOptions]] = field(default_factory=list)
    sensors: t.List[t.Tuple[str, CacheableSensorOptions]] = field(default_factory=list)
    asset_checks: t.List[t.Tuple[str, CacheableAssetCheckOptions]] = field(
        default_factory=list
    )
    assets: t.List[t.Tuple[str, CacheableAssetOptions]] = field(default_factory=list)
    multi_assets: t.List[t.Tuple[str, CacheableMultiAssetOptions]] = field(
        default_factory=list
    )


class CacheableDagsterContext:
    """Provides a way to create cacheable asset factories from one or more generateor functions."""

    def __init__(self, name: str, resources: ResourcesContext, cache: CacheBackend):
        self.name = name
        self._cache = cache
        self._resources = resources
        self._job_handlers: t.Dict[str, t.Tuple[t.Callable, dict]] = {}
        self._sensor_handlers: t.Dict[str, t.Tuple[t.Callable, dict]] = {}
        self._asset_check_handlers: t.Dict[str, t.Tuple[t.Callable, dict]] = {}
        self._asset_handlers: t.Dict[str, t.Tuple[t.Callable, dict]] = {}
        self._multi_asset_handlers: t.Dict[str, t.Tuple[t.Callable, dict]] = {}

        self._job_bindings: list[t.Tuple[str, CacheableJobOptions]] = []
        self._asset_bindings: list[t.Tuple[str, CacheableAssetOptions]] = []
        self._sensor_bindings: list[t.Tuple[str, CacheableSensorOptions]] = []
        self._asset_check_bindings: list[t.Tuple[str, CacheableAssetCheckOptions]] = []
        self._multi_asset_bindings: list[t.Tuple[str, CacheableMultiAssetOptions]] = []

        self._generators: list[CacheableDagsterObjectGenerator] = []

    def job(self, **kwargs: t.Any) -> t.Callable:
        """Create a cacheable job definition"""

        def _decorator(f: t.Callable) -> t.Callable:
            self._job_handlers[f.__name__] = (f, kwargs)
            return f

        return _decorator

    def sensor(self, **kwargs: t.Any) -> t.Callable:
        def _decorator(f: t.Callable[..., SensorDefinition]) -> t.Callable:
            self._sensor_handlers[f.__name__] = (f, kwargs)
            return f

        return _decorator

    def asset_check(self, **kwargs: t.Any) -> t.Callable:
        """Create a cacheable asset check definition"""

        def _decorator(f: t.Callable[..., AssetChecksDefinition]) -> t.Callable:
            self._asset_check_handlers[f.__name__] = (f, kwargs)
            return f

        return _decorator

    def asset(self, **kwargs: t.Any) -> t.Callable:
        """Create a cacheable asset definition"""

        def _decorator(f: t.Callable[..., CacheableAssetOptions]) -> t.Callable:
            # This decorator is used to create cacheable assets, so we don't need to do anything here.
            self._asset_handlers[f.__name__] = (f, kwargs)
            return f

        return _decorator

    def multi_asset(self, **kwargs: t.Any) -> t.Callable:
        """Create a cacheable multi-asset definition"""

        def _decorator(f: t.Callable[..., CacheableMultiAssetOptions]) -> t.Callable:
            # This decorator is used to create cacheable multi-assets, so we don't need to do anything here.
            return f

        return _decorator

    def add_generator(
        self,
        generator: CacheableDagsterObjectGenerator,
    ):
        self._generators.append(generator)

    def emit_job(self, handler_name: str, job_options: CacheableJobOptions):
        """Emit a job definition from the cacheable context."""
        if handler_name not in self._job_handlers:
            raise ValueError(f"Job handler {handler_name} not found.")
        self._job_bindings.append((handler_name, job_options))

    def emit_sensor(self, handler_name: str, sensor_options: CacheableSensorOptions):
        """Emit a sensor definition from the cacheable context."""
        if handler_name not in self._sensor_handlers:
            raise ValueError(f"Sensor handler {handler_name} not found.")
        self._sensor_bindings.append((handler_name, sensor_options))

    def emit_asset_check(
        self, handler_name: str, asset_check_options: CacheableAssetCheckOptions
    ):
        """Emit an asset check definition from the cacheable context."""
        if handler_name not in self._asset_check_handlers:
            raise ValueError(f"Asset check handler {handler_name} not found.")
        self._asset_check_bindings.append((handler_name, asset_check_options))

    def emit_asset(self, handler_name: str, asset_options: CacheableAssetOptions):
        """Emit an asset definition from the cacheable context."""
        if handler_name not in self._asset_handlers:
            raise ValueError(f"Asset handler {handler_name} not found.")
        self._asset_bindings.append((handler_name, asset_options))

    def load_bindings_from_cache(self):
        """Load the bindings from cache. This will load all the jobs, sensors,
        asset checks, and assets that were emitted from the cacheable context."""
        # This is a placeholder for loading the bindings from cache.
        # In a real implementation, this would load the bindings from a cache
        # and return them.
        bindings = self._cache.retrieve_object(
            self.name, CacheableDagsterContextBindings
        )
        self._job_bindings = bindings.jobs
        self._sensor_bindings = bindings.sensors
        self._asset_check_bindings = bindings.asset_checks
        self._asset_bindings = bindings.assets
        self._multi_asset_bindings = bindings.multi_assets

    def store_bindings_to_cache(self):
        """Store the bindings to cache. This will store all the jobs, sensors,
        asset checks, and assets that were emitted from the cacheable context."""
        bindings = CacheableDagsterContextBindings(
            jobs=self._job_bindings,
            sensors=self._sensor_bindings,
            asset_checks=self._asset_check_bindings,
            assets=self._asset_bindings,
            multi_assets=self._multi_asset_bindings,
        )
        self._cache.store_object(self.name, bindings)

    def load(self):
        # Attempt to load this cacheable context from cache
        try:
            self.load_bindings_from_cache()
        except CacheInvalidError:
            # If that fails, we will run the generators to create all the objects for
            # this cacheable context.
            for generator in self._generators:
                self._resources.run(
                    generator, additional_inject={"cache_context": self}
                )

            # After running the generators, we will store the bindings in cache.
            self.store_bindings_to_cache()

        return self.asset_factory_response_from_bindings()

    def asset_factory_response_from_bindings(self) -> AssetFactoryResponse:
        """Create an AssetFactoryResponse from the bindings."""
        assets = [
            options.as_dagster_asset(
                self._asset_handlers[handler_name][0],
                **self._asset_handlers[handler_name][1],
            )
            for handler_name, options in self._asset_bindings
        ]
        sensors = [
            options.as_dagster_sensor(
                self._sensor_handlers[handler_name][0],
                **self._sensor_handlers[handler_name][1],
            )
            for handler_name, options in self._sensor_bindings
        ]
        jobs: t.List[FactoryJobDefinition] = [
            options.as_dagster_job(
                self._job_handlers[handler_name][0],
                **self._job_handlers[handler_name][1],
            )
            for handler_name, options in self._job_bindings
        ]
        checks = [
            options.as_dagster_asset_check(
                self._asset_check_handlers[handler_name][0],
                **self._asset_check_handlers[handler_name][1],
            )
            for handler_name, options in self._asset_check_bindings
        ]
        return AssetFactoryResponse(
            assets=assets,
            sensors=sensors,
            jobs=jobs,
            checks=checks,
        )


def cacheable_asset_factory(
    f: t.Callable[..., CacheableDagsterContext],
) -> EarlyResourcesAssetFactory:
    """A decorator that creates a cacheable asset factory from a generator function.

    This decorator will create a cacheable asset factory that can be used to
    create assets that can be cached and retrieved from the cache.
    """

    @early_resources_asset_factory(caller_depth=2)
    def _factory(resources: ResourcesContext) -> AssetFactoryResponse:
        context = CacheableDagsterContext(
            name=f.__name__,
            resources=resources,
            cache=resources.resolve("cache"),
        )
        resources.run(f, additional_inject={"cache_context": context})
        return context.load()

    return _factory
