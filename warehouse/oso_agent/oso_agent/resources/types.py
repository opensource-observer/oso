import typing as t

from ..util.config import AgentConfig, WorkflowConfig

V = t.TypeVar("V")


class ResolverEnabled(t.Protocol):
    resolver: "ResourceResolver"

    def resolve_resource(
        self, name: str, default_factory: t.Optional[t.Callable[[], t.Any]]
    ) -> t.Any: ...


class ResourceDependency(t.Generic[V]):
    def __init__(self, default_factory: t.Optional[t.Callable[[], V]] = None):
        """A descriptor for resource dependencies in a workflow."""
        self._default_factory = default_factory

    def __set_name__(self, _owner, name):
        self._name = name

    def __get__(self, obj: ResolverEnabled | None, owner: t.Any) -> V:
        if obj is None:
            return self  # type: ignore
        return obj.resolve_resource(self._name, self._default_factory)

    def __set__(self, obj: t.Optional[object], value: V) -> None:
        raise AttributeError(
            f"Cannot set resource '{self._name}'. Resources are immutable after initialization."
        )

    def has_default_factory(self) -> bool:
        """Check if the resource has a default factory."""
        return self._default_factory is not None


class ResourceResolver(t.Protocol):
    """Protocol for a resource resolver that can resolve resources by name."""

    def add_resource(self, name: str, resource: t.Any) -> None: ...

    def get_resource(self, name: str) -> t.Any:
        """Get a resource by name."""
        ...

    def get_resources(self) -> dict[str, t.Any]:
        """Get all resources in the resolver."""
        ...

    def validate_for_required_resources(
        self, resources_dict: dict[str, type]
    ) -> list[tuple[str, str]]:
        """Check if all resources in the dictionary are available in the resolver."""
        ...

    def child_resolver(self, **additional_resources: t.Any) -> "ResourceResolver":
        """Extend the resolver with additional resources."""
        ...

    def merge_resolver(self, other: "ResourceResolver") -> "ResourceResolver":
        """Extend the resolver with resources from another resolver."""
        ...


ResolverFactory = t.Callable[
    [ResourceResolver, AgentConfig, WorkflowConfig], t.Awaitable[ResourceResolver]
]
