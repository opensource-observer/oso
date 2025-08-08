import copy
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
from oso_core.cache import Cache, CacheInvalidError
from oso_core.cache.types import StructuredCacheKey
from oso_dagster.config import DagsterConfig
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

    def has_resource_available(self, name: str) -> bool:
        """Check if this resource is available in the registry."""
        return name in self._registry._resources

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
        caller: inspect.FrameInfo | None = None,
        additional_annotations: t.Dict[str, t.Any] | None = None,
        dependencies: t.List["EarlyResourcesAssetFactory"] | None = None,
        tags: dict[str, str] | None = None,
    ):
        self._f = f
        self._caller = caller
        self.additional_annotations = additional_annotations or {}
        self._dependencies = dependencies or []
        self._tags = tags or {}

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
                additional_inject=dict(
                    dependencies=dependencies, factory_caller=self._caller
                ),
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

    @property
    def tags(self) -> dict[str, str]:
        """Get the tags for the asset factory."""
        return self._tags.copy()


def early_resources_asset_factory(
    *,
    caller_depth: int = 1,
    additional_annotations: t.Optional[t.Dict[str, t.Any]] = None,
    dependencies: t.Optional[t.List[EarlyResourcesAssetFactory]] = None,
    tags: dict[str, str] | None = None,
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


C = t.TypeVar("C", bound=BaseModel, covariant=True)


class CacheableDagsterObjectGenerator(t.Protocol[C]):
    def __call__(self, *args, **kwargs) -> C: ...

    __name__: str


type CacheableDagsterObjectHydrator = t.Callable[..., AssetFactoryResponse]


class CacheableDagsterObjectKey(StructuredCacheKey):
    cache_key_metadata: dict[str, str]
    name: str
    sub_name: str = ""


class CacheableDagsterContext:
    """Provides a way to create cacheable asset factories from one or more generateor functions."""

    def __init__(self, name: str, resources: ResourcesContext, cache: Cache):
        self._name = name
        self._cache = cache
        self._resources = resources

        self._generators: dict[
            str,
            t.Tuple[CacheableDagsterObjectGenerator, t.Type[BaseModel], dict[str, str]],
        ] = {}
        self._rehydrator: t.Callable[..., AssetFactoryResponse] | None = None

    def register_generator(
        self,
        *,
        cacheable_type: t.Type[C],
        name: str = "",
        extra_cache_key_metadata: dict[str, str] | None = None,
    ) -> t.Callable[..., None]:
        def _decorator(
            generator: CacheableDagsterObjectGenerator[C],
        ) -> None:
            """A decorator that registers a generator function to the cacheable context."""
            generator_name = name or generator.__name__
            self._generators[generator_name] = (
                generator,
                cacheable_type,
                extra_cache_key_metadata or {},
            )

        return _decorator

    def register_hydrator(self) -> t.Callable[..., None]:
        """A decorator that registers a rehydrator function to the cacheable context."""

        def _decorator(
            f: t.Callable[..., AssetFactoryResponse],
        ) -> None:
            """A decorator that registers a rehydrator function to the cacheable context."""
            if self._rehydrator is not None:
                raise ValueError("Rehydrator already registered.")
            self._rehydrator = f

        return _decorator

    def load(self, cache_key_metadata: dict[str, str]):
        """Load the cacheable context.

        For all of the expected annotations in the rehydrator, we will run
        either load from cache or run the generator functions and then inject
        that into the rehydrator.
        """

        if self._rehydrator is None:
            raise ValueError("Rehydrator not registered.")

        resources = self._resources

        generated_objects: t.Dict[str, BaseModel] = {}

        # Get all the annotations from the rehydrator function
        annotations = self._rehydrator.__annotations__
        for key, value in annotations.items():
            if key == "return":
                continue

            if key == ResourcesContext.resources_keyword_name:
                # If the key is the resources context, we will inject the resources context
                # into the rehydrator.
                continue

            if key in self._generators and resources.has_resource_available(key):
                raise ValueError(
                    f"Resource {key} is already registered as a generator, "
                    "but is also expected to be resolved from the resources context."
                    "this is ambiguous and should be resolved by the caller."
                )

            # First check if the key is one of the registered generators
            if key in self._generators:
                generator, cacheable_type, extra_cache_key_metadata = self._generators[
                    key
                ]
                if value is not cacheable_type:
                    raise ValueError(
                        f"Generator {key} is registered with type {cacheable_type}, "
                        f"but the rehydrator expects type {value}."
                    )

                generator_cache_key_metadata = copy.deepcopy(cache_key_metadata)
                generator_cache_key_metadata.update(extra_cache_key_metadata)

                cache_key = CacheableDagsterObjectKey(
                    cache_key_metadata=generator_cache_key_metadata,
                    name=self._name,
                    sub_name=key,
                )

                try:
                    # Try to load the object from cache
                    obj = self._cache.retrieve_object(cache_key, cacheable_type)
                except CacheInvalidError:
                    # If the object is not in cache, we will run the generator
                    obj = resources.run(
                        generator, additional_inject={"cache_context": self}
                    )
                    self._cache.store_object(cache_key, obj)

                generated_objects[key] = obj

        # Run the rehydrator with the loaded bindings
        return resources.run(self._rehydrator, additional_inject=generated_objects)


def cacheable_asset_factory(tags: dict[str, str] | None = None):
    def _decorator(
        f: t.Callable[..., CacheableDagsterContext],
    ) -> EarlyResourcesAssetFactory:
        """A decorator that creates a cacheable asset factory from a generator function.

        This decorator will create a cacheable asset factory that can be used to
        create assets that can be cached and retrieved from the cache.
        """

        @early_resources_asset_factory(caller_depth=2, tags=tags)
        def _factory(
            resources: ResourcesContext, cache: Cache, factory_caller: inspect.FrameInfo
        ) -> AssetFactoryResponse:
            context = CacheableDagsterContext(
                name=f.__name__,
                resources=resources,
                cache=cache,
            )
            resources.run(f, additional_inject={"cache_context": context})

            return context.load(
                cache_key_metadata=dict(
                    filename=factory_caller.filename,
                )
            )

        return _factory

    return _decorator
