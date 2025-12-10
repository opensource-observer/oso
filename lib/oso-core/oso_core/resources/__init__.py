import typing as t
from dataclasses import dataclass
from graphlib import TopologicalSorter

import structlog

logger = structlog.get_logger(__name__)


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

    def add_singleton(self, name: str, value: t.Any):
        """Add an unchanging global singleton value as a resource factory
        without having to make a full factory function."""

        if name in self._resources:
            raise ValueError(f"Resource factory with name {name} already exists.")

        def _constant_factory() -> t.Any:
            return value

        self._resources[name] = ResourceFactory(
            name=name,
            factory=_constant_factory,
            dependencies={},
            return_type=type(value),
        )
        self._resources_dag[name] = set()

    def add(self, resource_factory: ResourceFactory, override: bool = False):
        """Add a resource factory to the early resources container."""
        if resource_factory.name == "resources":
            raise ValueError(
                "Resource factory with name 'resources' is reserved and cannot be used."
            )

        if resource_factory.name in self._resources and not override:
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

        if name == ResourcesContext.resources_keyword_name:
            return self

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
